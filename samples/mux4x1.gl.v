module mux4x1 (a, b, c, d, sel, y);

input [1:0] a;
input [1:0] b;
input [1:0] c;
input [1:0] d;
input [1:0] sel;
output [1:0] y;

wire vdd = 1'b1;
wire gnd = 1'b0;

NAND3X1 NAND3X1_1 ( .A(sel[0]), .B(sel[1]), .C(d[1]), .Y(_0_) );
INVX1 INVX1_1 ( .A(sel[0]), .Y(_1_) );
NAND3X1 NAND3X1_2 ( .A(sel[1]), .B(c[1]), .C(_1_), .Y(_2_) );
AND2X2 AND2X2_1 ( .A(_2_), .B(_0_), .Y(_3_) );
NOR2X1 NOR2X1_1 ( .A(sel[0]), .B(sel[1]), .Y(_4_) );
NOR2X1 NOR2X1_2 ( .A(sel[1]), .B(_1_), .Y(_5_) );
AOI22X1 AOI22X1_1 ( .A(a[1]), .B(_4_), .C(b[1]), .D(_5_), .Y(_6_) );
NAND2X1 NAND2X1_1 ( .A(_3_), .B(_6_), .Y(_11__1_) );
NAND3X1 NAND3X1_3 ( .A(sel[0]), .B(sel[1]), .C(d[0]), .Y(_7_) );
NAND3X1 NAND3X1_4 ( .A(sel[1]), .B(c[0]), .C(_1_), .Y(_8_) );
AND2X2 AND2X2_2 ( .A(_8_), .B(_7_), .Y(_9_) );
AOI22X1 AOI22X1_2 ( .A(a[0]), .B(_4_), .C(b[0]), .D(_5_), .Y(_10_) );
NAND2X1 NAND2X1_2 ( .A(_9_), .B(_10_), .Y(_11__0_) );
BUFX2 BUFX2_1 ( .A(_11__0_), .Y(y[0]) );
BUFX2 BUFX2_2 ( .A(_11__1_), .Y(y[1]) );
endmodule
