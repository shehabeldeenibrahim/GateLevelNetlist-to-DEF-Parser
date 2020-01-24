module mux4x1(input[1:0] a, b, c, d, input[1:0] sel, output[1:0] y);

assign y = 	(sel==0) ? a : 
		(sel==1) ? b :
		(sel==2) ? c : 
		(sel==3) ? d : 0;  

endmodule
