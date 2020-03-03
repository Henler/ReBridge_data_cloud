
 
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.FileInputStream; 
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellType;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import java.util.HashMap;
import java.util.Vector;
import java.lang.String;
import org.apache.poi.openxml4j.util.ZipSecureFile;

import com.google.gson.Gson;;
 
public class ExcelReader {
     
    public void readExcel(String fileName){
    	ZipSecureFile.setMinInflateRatio(0.005);
        try {
        	String extension = fileName.substring(fileName.lastIndexOf(".") + 1, fileName.length());
        	FileInputStream fileStream = new FileInputStream(fileName);
        	//System.out.println(extension);
        	String xssf = "xlsx";
        	String hssf = "xls";
        	Workbook workbook;
        	if(xssf.equalsIgnoreCase(extension)){
        		workbook = new XSSFWorkbook(fileStream);
            	//XSSFWorkbook is for Excel 2007 and above (.xlsx)
            } else{
            	workbook = new HSSFWorkbook(fileStream);
            } 
            //WorkBook workbook = new HSSFWorkbook(fileName);//HSSFWorkbook is for Excel 2003 (.xls)
            Vector<HashMap<String, Object>> sh_vec = new Vector<HashMap<String, Object>>();
            for (int i = 0; i < workbook.getNumberOfSheets(); i++)
            {	
            	SheetReader sh = new SheetReader();
                sh.read_sheet_from_ind(workbook, i);
            	if(sh.getStatus() == 1) {
            		HashMap<String, Object> h_map = new HashMap<String, Object>();
            		h_map.put("Vals", sh.vals);
            		h_map.put("Types", sh.types);
            		h_map.put("Name", sh.getSheet_name());
            		sh_vec.add(h_map);
            		
            	}

            }
            Gson gson = new Gson();
            System.out.print(gson.toJson(sh_vec));

        } catch (FileNotFoundException e) {
            System.out.println("File is not available.");
            e.printStackTrace();
        } catch (IOException e){
            System.out.println("Problem reading file from directory.");
            e.printStackTrace();
        }
    }
     
    public static void main(String[] args) {
        new ExcelReader().readExcel(args[0]);
    }
    

}