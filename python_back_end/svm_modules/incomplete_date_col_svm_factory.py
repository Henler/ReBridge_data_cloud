from sklearn import svm
from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
from python_back_end.data_cleaning.cleaning_utils import *
import pandas as pd
from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.utilities.state_handling import DataHolder
from python_back_end.utilities.sheet_io import ExcelLoader
from python_back_end.triangle_formatting.triangle_utils import SheetPreProcessor
from python_back_end.logConfig import LOGGING
import logging.config
import pickle
import jsonpickle

logging.config.dictConfig(LOGGING)



def main():
    path_x = pdir.RESOURCES_DIR + '/svm_learning_data/incomplete_date_col_data_x.csv'
    x = np.genfromtxt(path_x, dtype=np.float64, delimiter=',')
    path_y = pdir.RESOURCES_DIR + '/svm_learning_data/incomplete_date_col_data_y.csv'
    y = np.genfromtxt(path_y, dtype=np.float64, delimiter=',')
    #print(x_y)
    #x = x_y[:, :-1]
    #y = x_y[:, -1]
    #print(x)
    #print(y)

    #clf = svm.SVC(random_state=0, tol=1e-5, C=1000, gamma="auto")
    clf = svm.LinearSVC(random_state=0, tol=1e-5, class_weight='balanced')

    clf.fit(x, y)
    with open(pdir.RESOURCES_DIR + '/svm_learning_data/date_svm.pickle', "wb") as temp_file:
          pickle.dump(jsonpickle.encode(clf), temp_file)
    #print(clf.coef_)
    #proba = clf.predict_proba(x)
    prediction = clf.predict(x)
    difference = prediction-y
    print(prediction)
    print(y)
    print(clf.decision_function(x))


def generate_training_data():

    files = [
        #Add files here

            ]
    files = [pdir.RESOURCES_DIR + "/raw_test_files/" + file[0] for file in files]
    for file in files:
        run_test_per_file_name(file)

    x_y = np.genfromtxt(pdir.SVM_LOG_FILE, dtype=np.float64, delimiter=',')
    x = x_y[:, :-1]
    y = x_y[:, -1]
    np.savetxt(pdir.RESOURCES_DIR + '/svm_learning_data/incomplete_date_col_data_x.csv', x, delimiter=",")
    np.savetxt(pdir.RESOURCES_DIR + '/svm_learning_data/incomplete_date_col_data_y.csv', y, delimiter=",")
    #pass


def run_test_per_file_name(file_name):

    print(file_name)
    logger = logging.getLogger("svm_writer")
    sr_list, file_name = ExcelLoader.load_excel(file_name)
    dh = DataHolder(file_name.split(".")[0])
    for sr in sr_list:
        dh.add_sheet(sr.sheet_name, pd.DataFrame(columns=sr.headers, data=sr.row_vals),
                     pd.DataFrame(columns=sr.headers, data=sr.xls_types), orig_sheet_name=sr.sheet_name)
    dh = SheetPreProcessor.pre_strip(dh)
    DateColIdentifier.identify_and_gen_date_cols(dh, replace_col=False, svm_logger=logger)
    #logger.info('9, 9, 9, 9, 9')

def run_cleaning_per_file_name(file_name):

    print(file_name)
    logger = logging.getLogger("svm_writer")
    sr_list, file_name = ExcelLoader.load_excel(file_name)
    dh = DataHolder(file_name.split(".")[0])
    for sr in sr_list:
        dh.add_sheet(sr.sheet_name, pd.DataFrame(columns=sr.headers, data=sr.row_vals),
                     pd.DataFrame(columns=sr.headers, data=sr.xls_types), orig_sheet_name=sr.sheet_name)
    dh, meta_dh = HeaderFinder.find_headers(dh)

    # save original state
    dh.create_memento()

    # Find and remove deviating rows
    dh = DevRowFinder.delete_deviating_rows(dh)

    # Identify and add date col
    DateColIdentifier.identify_and_gen_date_cols(dh, svm_logger=logger)

    #logger.info('9, 9, 9, 9, 9')

if __name__ == '__main__':
    #generate_training_data()
    main()