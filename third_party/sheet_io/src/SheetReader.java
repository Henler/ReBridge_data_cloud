import java.util.Arrays;
import org.apache.poi.ss.usermodel.DateUtil;
import org.apache.poi.ss.usermodel.CellType;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.ss.util.CellRangeAddress;
import java.text.SimpleDateFormat;

public class SheetReader {
	
   public void read_sheet_from_ind(Workbook wb, int ind) {

        int n_sheets = wb.getNumberOfSheets();
        // Check that we haven't come to the end of the sheet
        if (ind < n_sheets) {
            this.status = 0;
            String sheet_name = wb.getSheetName(ind);
            Sheet sheet = wb.getSheetAt(ind);
            // Check that the sheet contains a minimum of 10 rows
            if (sheet.getFirstRowNum() != sheet.getLastRowNum()) {
            	int[] row_range = new int[2];          			
                row_range[0] = 0;
                row_range[1] = sheet.getLastRowNum()+1;
                int nrows = (row_range[1] - row_range[0]);
                int[][] col_ranges = new int[2][nrows];
                for(int i = row_range[0]; i <row_range[1]; i++) {
                    Row row = sheet.getRow(i);
                    if(row != null) {
                    	col_ranges[0][i] = 0;
                    	col_ranges[1][i] = row.getLastCellNum();
                    }else {
                    	col_ranges[0][i] = 0;
                    	col_ranges[1][i] = 0;
                    }
                }
                //col_ranges = np.array(col_ranges)
                int[] col_range = new int[2]; 
                col_range[0] = Arrays.stream(col_ranges[0]).min().getAsInt();
                col_range[0] = Math.max(0, col_range[0]);
                col_range[1] = Arrays.stream(col_ranges[1]).max().getAsInt();
                int ncols = col_range[1] - col_range[0];
                if(nrows >= this.MIN_NUM_ROWS_DATA_SHEET && ncols >= this.MIN_NUM_COLS_DATA_SHEET) {
                    this.status = 1;
                    this.sheet_name = sheet_name;
                    this.read_sheet(sheet, col_ranges, row_range, ncols);
                }
            }
            
        }else {
            this.status = 0;
        }
   }
   
   private void read_sheet(Sheet sheet, int[][] col_ranges, int [] row_range, int ncols) {
       SimpleDateFormat date_formatter = new SimpleDateFormat("yyyy-MM-dd");
       //DateUtil dateUtil = new DateUtil();
       int order_index = 1;
       this.vals = new Object[row_range[1] - row_range[0]][ncols + 1];
       for(int i = 0; i < this.vals.length; i++) {
    	   Arrays.fill(this.vals[i], "");
       }
       
       this.types = new int[row_range[1] - row_range[0]][ncols + 1];
       for (int row_ind = row_range[0]; row_ind < row_range[1]; row_ind++) {
           Row xl_row = sheet.getRow(row_ind);
           int row_tab_ind = row_ind - row_range[0];
           for (int col_ind = col_ranges[0][row_tab_ind]; col_ind < col_ranges[1][row_tab_ind]; col_ind++) {
               Cell cell = xl_row.getCell(col_ind);
               int col_tab_ind = col_ind - col_ranges[0][row_tab_ind];
               if(cell == null) {
                   this.vals[row_tab_ind][col_tab_ind] = "";
               } else {
                   CellType cell_type = cell.getCellType();
                   if (cell_type == CellType.FORMULA) {
                	   cell_type = cell.getCachedFormulaResultType();
                   }
                   if (cell_type == CellType.STRING) {
                	   this.vals[row_tab_ind][col_tab_ind] = cell.getStringCellValue();
                	   this.types[row_tab_ind][col_tab_ind] = TypeDefs.STRING.getValue();
                   } else if (cell_type == CellType.NUMERIC) {
                       if (DateUtil.isCellDateFormatted(cell)) {
                           String temp_date = date_formatter.format(cell.getDateCellValue());
                           this.vals[row_tab_ind][col_tab_ind] = temp_date;
                           //Now all dates are strings!!!
                           this.types[row_tab_ind][col_tab_ind] = TypeDefs.STRING.getValue();
                       }else {
                    	   this.vals[row_tab_ind][col_tab_ind] = cell.getNumericCellValue();
                    	   this.types[row_tab_ind][col_tab_ind] = TypeDefs.FLOAT.getValue();
                    	   
                       }
                   } else if (cell_type == CellType.ERROR) {
                	   this.vals[row_tab_ind][col_tab_ind] = "nan";
                       this.types[row_tab_ind][col_tab_ind] = TypeDefs.ERROR.getValue();
                   } else  {
                	   this.vals[row_tab_ind][col_tab_ind] = "";
                	   this.types[row_tab_ind][col_tab_ind] = TypeDefs.EMPTY_STRING.getValue();
                   }
               }
               if(this.vals[row_tab_ind][col_tab_ind] == "") {
            	   this.types[row_tab_ind][col_tab_ind] = TypeDefs.EMPTY_STRING.getValue();
               }
//               if( row_ind == row_range[1] - 1) {
//        		   System.out.println(this.vals[row_tab_ind][col_tab_ind]);
//        		   System.out.println(this.types[row_tab_ind][col_tab_ind]);
//        		   System.out.println(this.vals[row_tab_ind][col_tab_ind] == "");
//        	   }
           }
           this.vals[row_tab_ind][ncols] = row_tab_ind + 1;
           this.types[row_tab_ind][ncols] = TypeDefs.ORDER.getValue();


       }

       handle_merged_cells(sheet);
   }
   
   private void handle_merged_cells(Sheet sheet) {
	   //java.util.List<CellRangeAddress> merged_regions = sheet.getMergedRegions();
	    	for (int i = 0 ; i < sheet.getNumMergedRegions() ; i++) {
	    	//don't merge beyond sheet
	    		CellRangeAddress merged_region = sheet.getMergedRegion(i);
	    		int c_f = merged_region.getFirstColumn();
	    		int c_l = merged_region.getLastColumn()+1;
	    		c_l = Math.min(c_l, this.vals[0].length -1);
	    		int r_f = merged_region.getFirstRow();
	    		int r_l = merged_region.getLastRow()+1;
	    		Object fill_element = this.vals[r_f][c_f];
	    		int fill_type = this.types[r_f][c_f];
	    		for(int r_ind = r_f; r_ind < r_l; r_ind++) {
	    			for (int c_ind = c_f; c_ind < c_l; c_ind ++) {
	    				this.vals[r_ind][c_ind] = fill_element;
	    				this.types[r_ind][c_ind] = fill_type;
	    			}
	    		}
		    	//self.row_vals[r_r[0]:r_r[1], c_r[0]:c_r[1]] = self.row_vals[r_r[0], c_r[0]]
		    	//self.xls_types[r_r[0]:r_r[1], c_r[0]:c_r[1]] = self.xls_types[r_r[0], c_r[0]]
	    	}
   }
    
	public int getStatus() {
		return status;
	}
	public void setStatus(int status) {
		this.status = status;
	}
	public String getSheet_name() {
		return sheet_name;
	}
	public void setSheet_name(String sheet_name) {
		this.sheet_name = sheet_name;
	}
   	
   	public Object[][] vals;
   	public int[][] types;
    private int status;
    private String sheet_name;
    public int MIN_NUM_ROWS_DATA_SHEET = 8;
    public int MIN_NUM_COLS_DATA_SHEET = 3;
}

