// FSM_Grid_Stability_v2.v
// DACS -- Finite State Machine
module FSM_Grid_Stability_v2 (
    input  wire FSM_CLK,
    input  wire GRID_OK,
    output wire STABILITY_DONE,
    output wire TIMER_05,
    output wire GRID_FALL,
    output wire S1,
    output wire S0,
    output wire NOT_S1,
    output wire NOT_S0
);

    reg S1_r, S0_r;
    wire D0_next, D1_next;
    assign S1     = S1_r;
    assign S0     = S0_r;
    assign NOT_S1 = ~S1_r;
    assign NOT_S0 = ~S0_r;

    always @(posedge FSM_CLK) begin
        S1_r <= D1_next;
        S0_r <= D0_next;
    end

    // ---- Edge detector ----
    reg GRID_delay_r;
    always @(posedge FSM_CLK) GRID_delay_r <= GRID_OK;
    wire NOT_GRID_OK = ~GRID_OK;
    wire GRID_delay  = GRID_delay_r;
    assign GRID_FALL = NOT_GRID_OK & GRID_delay;

    // ---- Recovery counter (counter_50) ----
    reg [2:0] cnt50;
    always @(posedge FSM_CLK) begin
        if (NOT_GRID_OK)
            cnt50 <= 3'd0;
        else if (GRID_OK)
            cnt50 <= (cnt50 == 3'd7) ? 3'd0 : cnt50 + 3'd1;
    end
    wire QA50 = cnt50[0], QB50 = cnt50[1], QC50 = cnt50[2];
    assign STABILITY_DONE = (QA50 & QC50) | (QB50 & QC50);

    // ---- Fault counter (counter_05) ----
    reg [2:0] cnt05;
    always @(posedge FSM_CLK) begin
        if (GRID_FALL)
            cnt05 <= 3'd0;
        else if (NOT_GRID_OK)
            cnt05 <= (cnt05 == 3'd5) ? 3'd0 : cnt05 + 3'd1;
    end
    wire QA05 = cnt05[0], QB05 = cnt05[1], QC05 = cnt05[2];
    assign TIMER_05 = ~(QA05 & QB05) & ~QC05;

    // ---- Next-state logic ----
    wire NOT_STAB_DONE = ~STABILITY_DONE;
    wire NOT_TIMER_05  = ~TIMER_05;

    wire D0_T1 = NOT_S1 & NOT_S0 & NOT_GRID_OK;
    wire D0_T2 = S1_r   & NOT_S0 & GRID_OK;
    wire D0_T3 = NOT_S1 & S0_r   & TIMER_05 & NOT_GRID_OK;
    wire D0_T4 = S1_r   & S0_r   & NOT_STAB_DONE & GRID_OK;
    assign D0_next = D0_T1 | D0_T2 | D0_T3 | D0_T4;

    wire D1_T1 = NOT_S1 & S0_r & NOT_TIMER_05 & NOT_GRID_OK;
    wire D1_T2 = S1_r   & NOT_S0;
    wire D1_T3 = S1_r   & S0_r & NOT_STAB_DONE;
    assign D1_next = D1_T1 | D1_T2 | D1_T3;
endmodule
