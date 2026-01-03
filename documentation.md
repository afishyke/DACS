# DACS: Dynamic AC Switching

## 1. Introduction
DACS is an electronic system designed to monitor the stability of the AC power grid and automatically manage power distribution to loads. It detects grid failures based on voltage and frequency deviations, switches to a battery backup for essential loads, and sheds non-essential loads to conserve power.

The system incorporates delays and counters to prevent rapid switching (chattering) during brief grid fluctuations. It is built entirely using discrete analog and digital components—comparators, timers, logic gates, and counters—without the use of microcontrollers.

**Applications:**
* Uninterruptible Power Supplies (UPS)
* Off-grid power management
* Critical load protection (medical equipment, essential lighting)

---

## 2. Project Structure
The repository contains the following primary directories:

* **/SCHEMATIC/**: Contains the KiCad hardware design files, including schematics (`.kicad_sch`), PCB layouts (`.kicad_pcb`), and generated PDF exports.
* **/Simulation/logisim/**: Contains the `FSM_Grid_Stabilityiteration_FINAL.XML` file for simulating the logic in Logisim.

---

## 3. System Overview
The project is divided into three main blocks:

1.  **Block 1 - Inputs:** Handles power conversion, grid monitoring (voltage/frequency), and battery status checking.
2.  **Block 2 - Logic:** Processes input signals using timers, inverters, AND gates, and counters to implement the Finite State Machine (FSM).
3.  **Block 3 - Outputs:** Drives relays to connect or disconnect power sources to the loads.

### Key Signals
*   **GRID_OK:** High when grid voltage and frequency are within acceptable limits.
*   **BATT_GOOD:** High when battery voltage is sufficient.
*   **FSM_CLK:** ~4.8Hz clock for timing operations.

---

## 4. Block Explanations

### 4.1 Block 1 - Inputs
*   **Rectifier and Power Supply:** Converts 12V AC to DC via bridge rectifier and LM7805 regulator for a stable +5V logic supply.
*   **Window Comparator (Voltage Check):** Uses dual LM393 comparators to verify if the scaled `GRID_SENSE` signal is between ~2.78V (lower) and ~4.08V (upper).
*   **Frequency Window:** Monitors for a 50Hz target. It converts AC to a square wave and uses monostable-like circuits to ensure pulses fall within a valid time window (typically 45Hz–55Hz).
*   **Battery Monitor:** Compares battery voltage against a reference. If above ~10V, `BATT_GOOD` is asserted.

### 4.2 Block 2 - Logic
This block implements the decision-making logic and timing delays:
*   **Clock Generator:** LM555 in astable mode (Ra=1kΩ, Rb=150kΩ, C=1μF) producing ~4.8Hz.
*   **Counters (74HC163N):**
    *   **COUNTER_.05:** Provides a ~0.63s delay (3 clock cycles) for failure confirmation/debounce.
    *   **COUNTER_.50:** Provides a ~1.05s delay (5 clock cycles) for grid stabilization confirmation.
*   **Gate Logic:** 74HC08 (AND) and 74HC04 (NOT) gates are used to define the FSM states and latching behavior.

### 4.3 Block 3 - Outputs
*   **Relay Drivers:** 2N2219 NPN transistors drive SPST-NO relays.
*   **Relay Logic:**
    *   **GRID Relay:** Connects loads to the mains when grid is healthy and stable.
    *   **ESSENTIAL Relay:** Remains active during battery mode.
    *   **NON-ESSENTIAL Relay:** Sheds load during grid failure to preserve battery.

---

## 5. FSM Definition (Core Logic)

The system uses a 2-bit Finite State Machine:

| State | S1 | S0 | Meaning |
| :--- | :--- | :--- | :--- |
| **ST00** | 0 | 0 | **Grid Mode:** Normal operation. |
| **ST01** | 0 | 1 | **Debounce:** Grid failed, waiting to confirm. |
| **ST10** | 1 | 0 | **Battery Mode:** Essential loads only. |
| **ST11** | 1 | 1 | **Stabilization:** Grid returned, waiting to confirm stability. |

### Transitions
1.  **ST00 → ST01:** Triggered by `GRID_OK` falling low (grid failure detected).
2.  **ST01 → ST10:** Triggered after 0.63s if `GRID_OK` remains low (persistent failure).
3.  **ST10 → ST11:** Triggered by `GRID_OK` returning high (grid recovery).
4.  **ST11 → ST00:** Triggered after 1.05s if `GRID_OK` remains high (grid stable).

---

## 6. Key Equations and Calculations

### 555 Timer Frequency (FSM_CLK)
$$f = \frac{1.44}{(R_a + 2R_b) \cdot C} \approx 4.8\text{ Hz}}$$
$$T = \frac{1}{f} \approx 0.21\text{ s}}$$

### Delays
*   **Debounce (3 cycles):** $3 \times 0.21\text{s} \approx 0.63\text{s}$
*   **Stabilization (5 cycles):** $5 \times 0.21\text{s} \approx 1.05\text{s}$

### Voltage Thresholds (Scaled)
*   **Upper Threshold:** $\approx 4.08\text{V}$ (Typical for ~240V mains equivalent)
*   **Lower Threshold:** $\approx 2.78\text{V}$ (Typical for ~180V mains equivalent)
