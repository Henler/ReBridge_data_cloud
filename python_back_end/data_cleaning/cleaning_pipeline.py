from python_back_end.utilities.state_handling import SheetStateComparer
from python_back_end.data_cleaning.cleaning_utils import *


class CleaningPipeline:


    @staticmethod
    def clean_data_dh(dh):
        # Find the headers and remove them from the sheet
        dh, meta_dh = HeaderFinder.find_headers(dh)

        # save original state
        dh.create_memento()


        # Find and remove deviating rows
        dh = DevRowFinder.delete_deviating_rows(dh)

        # Identify and add date col
        dh = DateColIdentifier.identify_and_gen_date_cols(dh)

        # Rowwise errors
        dh = ErrorFinder.find_rowwise_additive_patterns(dh)

        # Colwise errors
        dh = ErrorFinder.find_colwise_additive_patterns(dh)

        # Detect sum row
        dh = SumRowFinder.detect_sum_row(dh)

        # Spellcheck
        dh = SpellCheck.correct_spelling(dh)

        # Add currency
        dh = CurrencyColGen.generate_currency_col(dh)

        # make new state memento
        dh.create_memento()

        diff_dict_list = SheetStateComparer.compare_states(dh.mementos[0], dh.mementos[1])

        return diff_dict_list, dh








