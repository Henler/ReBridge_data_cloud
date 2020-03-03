
public enum TypeDefs {	
	EMPTY_STRING(0),
	STRING(1),
	FLOAT(2),
	XL_DATE(3),
	BOOLEAN(4),
	ERROR(5),
	ZERO_FLOAT(6),
	STRING_DATE(7),
	ORDER(8),
	TRIANGLE_ELEMENT(9),
	ID_ELEMENT(10);
	private int value;
	   private TypeDefs(int value) {
	      this.value = value;
   }
   public int getValue() {
	      return value;
	   }
}
