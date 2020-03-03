import numpy as np

from python_back_end.data_cleaning.date_col_identifier import DateColIdentifier
from python_back_end.program_settings import PROGRAM_STRINGS as ps
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from python_back_end.definitions import SheetTypeDefinitions
from itertools import combinations
import logging
from python_back_end.utilities.state_handling import DataStruct, DataHolder
from python_back_end.data_cleaning.type_col_extracter import TypeColExtracter


class HeaderFinder:
    @staticmethod
    def find_headers(dh):
        meta_dh = DataHolder(dh.name + "_meta")
        for ds in dh:
            df_data, df_profiles = ds.df_data, ds.df_profiles
            bin_mat = df_profiles.values[:pp.N_POSSIBLE_HEADER_ROWS, ] == 1
            one_nums = np.sum(bin_mat, axis=1)
            # subtract identical strings
            for i in range(pp.N_POSSIBLE_HEADER_ROWS):
                sub = df_data.shape[1] - len(df_data.iloc[i, :].unique())
                one_nums[i] -= sub
            header_ind = np.argmax(one_nums)
            pd_ind = df_profiles.index[header_ind]
            headers = df_data.loc[[pd_ind]]
            HeaderFinder.insert_headers(headers, pd_ind, df_data, df_profiles)
            meta_ds = HeaderFinder.remove_leading_rows(ds, pd_ind)
            meta_dh.add_ds(meta_ds)
        return dh, meta_dh

    @staticmethod
    def insert_headers(headers, pd_ind, df_data, df_profiles):
            #cond = (headers != ps.ORDER_COL_NAME).any(axis=0)
            #headers = headers.loc[:, cond]
            rename_dict = dict()
            counter = 1
            for temp_col, header in headers.iteritems():
                temp_val = str(header.values[0])
                if "transformed" in temp_col:
                    # if available use padding as key to find other name
                    pad_key = temp_col[:pp.N_DIGITS_HEADER_PADDING + 2] + ps.HEADER_PLACE_HOLDER
                    matches = np.array([pad_key == el for el in headers.columns])
                    temp_val = headers.iloc[0, np.argmax(matches)]
                elif temp_val == '':
                    temp_val = 'Missing header #' + str(counter)
                    counter += 1
                # Dont push in the counter twice
                n_pad_dig = int(pp.N_DIGITS_HEADER_PADDING + 2)
                if len(str(temp_val)) >= n_pad_dig:
                    if temp_val[0:n_pad_dig] == str(temp_col)[0:n_pad_dig]:
                        temp_val = temp_val[n_pad_dig:]
                rename_dict[temp_col] = str(temp_col).replace(ps.HEADER_PLACE_HOLDER, str(temp_val))
            df_data.rename(columns=rename_dict, inplace=True)
            df_profiles.rename(columns=rename_dict, inplace=True)
            df_data.drop(labels=pd_ind, axis=0, inplace=True)
            df_profiles.drop(labels=pd_ind, axis=0, inplace=True)

    @staticmethod
    def remove_leading_rows(ds, dh_ind):

        leading = ds.df_data.index[ds.df_data.index < dh_ind]
        meta_data = ds.df_data.loc[leading, :]
        meta_profiles = ds.df_profiles.loc[leading, :]
        meta_ds = DataStruct(meta_data, meta_profiles, ds.name + "_meta")
        ds.df_data.drop(leading, inplace=True)
        ds.df_profiles.drop(leading, inplace=True)
        return meta_ds


class SpellCheck:
    @staticmethod
    def correct_spelling(dh):
        for dh_ind, df_data, df_profiles in dh.enumerate():
            # now just fix one spell mistake, Fire -> fire
            for index in df_data.index:
                for col in df_data.columns:
                    if isinstance(df_data.at[index, col], str):
                        if df_data.at[index, col] == "Fire":
                            df_data.at[index, col] = "fire"
            dh.update_with_ind(dh_ind, df_data, df_profiles)
        return dh


class DevRowFinder:

    @staticmethod
    def delete_deviating_rows(dh):
        for dh_ind, df_data, df_profiles in dh.enumerate():
            profiles = {}
            sep = ", "
            # make bool to ignore automatically generated cols
            head = df_profiles.head(1)
            bool = ((head != SheetTypeDefinitions.ORDER) & (head != SheetTypeDefinitions.STRING_DATE)).values.reshape((head.size,))
            for i, p_array in df_profiles.iterrows():
                types = p_array.values[bool]
                type_strings = [str(t) for t in types]
                if sep.join(type_strings) in profiles:
                    profiles[sep.join(type_strings)] += [i]
                else:
                    profiles[sep.join(type_strings)] = [i]

            def length(el):
                return len(el[1])
            common_profile = max(profiles.items(), key=length)[0]

            deviating_profiles = DevRowFinder.deviating_profiles(common_profile, profiles, sep)
            dev_rows = []
            for prof in deviating_profiles:
                for ind in profiles[prof]:
                    dev_rows.append(ind)


            # Remove them
            df_data.drop(dev_rows, inplace=True)
            df_profiles.drop(dev_rows, inplace=True)

            # now detect nulls

            nulls = DevRowFinder.null_rows(df_data, df_profiles)

            df_data.drop(nulls, inplace=True)
            df_profiles.drop(nulls, inplace=True)
            dh.update_with_ind(dh_ind, df_data, df_profiles)
        return dh

    @staticmethod
    def null_rows(df_data, df_profiles):
        nulls = list()
        for i in df_profiles.index:
            row = df_data.loc[i]
            profile = df_profiles.loc[i]
            num = 0
            str_nums = np.array(row)[profile == 2]
            for str_num in str_nums:
                num += float(str_num)
            if num == 0:
                nulls.append(i)
        return nulls

    @staticmethod
    def deviating_profiles(master, all, sep, frac=0.75):
        list_master = master.split(sep)
        deviant = list()
        for prof in all:
            listified = prof.split(sep)
            bool = np.array(list_master) == np.array(listified)
            sim = np.sum(bool) / len(bool)
            if sim < frac:
                deviant.append(prof)
        return deviant


class GeneralStringFormatter:

    @staticmethod
    def format(input):
        if isinstance(input, (float, int, np.float64)):
            if not np.isnan(input):
                integer = int(round(input))
                type = DateColIdentifier.match(str(integer))
                if type is 1:
                    return integer
                else:
                    return '{:,}'.format(integer)
        return input


# This class matches tags to existing headers
class TagMatcher:

    def __init__(self):
        self.regex_dict = dict()
        for tuple in SheetTypeDefinitions.TAG_OPTIONS:
            # self.regex_dict[tuple[0]] = ["/"+tuple[1]+"/i"]
            self.regex_dict[tuple[0]] = [tuple[1]]

    def match_headers(self, headers):
        tags = ["UN" for i in headers]
        match_dict = {
            "Total incurred": "LO",
            "Year transformed": "YR",
            "EML-band": "ETB",
            "Missing header #2": "ETB",
            "NO of EML": "NR",
            "Premium": "PR",
            "Commercial": "SEG",
            "Industrial": "SEG",
            "Missing header #1": "TAG"
        }

        for header, i in zip(headers, range(len(headers))):
            for key in match_dict.keys():
                if key in header:
                    tags[i] = match_dict[key]
        return tags


# This class searches for errors in sheets
class ErrorFinder:
    threshold = 0.7
    null_strs  = {'', '0', '0,0', '0.0', '_', '-'}

    @staticmethod
    def find_rowwise_additive_patterns(dh, tolerance=1):
        for dh_ind, df_data, df_profiles in dh.enumerate():
            #Check rowwise

            periods = [ErrorFinder.find_col_periodicity(col) for col in df_data.T.values]
            period_index = np.argmin(periods)
            period = periods[period_index]

            if np.isfinite(period):
                for index, prof in df_profiles.T.iterrows():
                    num_ratio = np.sum(prof == 2)/prof.size
                    if num_ratio > 0.9:

                        col = df_data[index].values.astype(float)
                        for start in range(period):
                            sum = np.zeros(col[start::period].size)
                            for i in range(period - 1):
                                temp = col[start + i::period]
                                if temp.size == sum.size - 1:
                                    sum = sum[:-1]
                                    # temp = np.append(temp, [0.0])
                                sum += temp

                            target = col[start + period - 1::period]
                            # check difference between sum and target
                            if sum.size == target.size + 1:
                                sum = sum[:-1]
                            bool = np.abs(target - sum) < tolerance
                            # check if it sums
                            ratio = np.sum(bool) / bool.size
                            if ratio > ErrorFinder.threshold:
                                # check if there are errors
                                if ratio < 1:
                                    df_data.loc[df_data.index[start + period - 1::period], index] = sum
                                    break
            dh.update_with_ind(dh_ind, df_data, df_profiles)
        return dh




    @staticmethod
    def find_col_periodicity(col, max_period=4):
        #Truncate (for avoiding unnecessary calculations
        trunc = np.minimum(col.size, 30)
        col = col[:trunc].astype(str)

        outperiod = float("inf")
        #Check for recurrent entries
        unique, counts = np.unique(col, return_counts=True)
        ratio = np.max(counts)/col.size
        if ratio > 0.5 or ratio < 0.1:
            return outperiod
        # create slices
        for period in range(2, max_period):
            for start in range(period):
                sliced_col = col[start::period]
                unique, counts = np.unique(sliced_col, return_counts=True)
                max_ind = np.argmax(counts)
                if not unique[max_ind] in ErrorFinder.null_strs:
                    periodicity = counts[max_ind]/len(sliced_col)
                    if periodicity > ErrorFinder.threshold:
                        outperiod = period
        return outperiod


    @staticmethod
    def find_colwise_additive_patterns(dh, tolerance=1):
        for dh_ind, ds in enumerate(dh):
            df_data, df_profiles = ds.df_data, ds.df_profiles
            logger = logging.getLogger("data_cloud_logger")

            # find set of numeric cols
            df_num = TypeColExtracter.extract_num_cols(df_data, df_profiles)
            if len(df_num.columns) >= 3:

                # Now test summabilities combinatorially!

                for header in df_num.columns:
                    other_cols = df_num.columns.delete(np.where(df_num.columns==header))
                    subsets = [np.array(sub_set) for sub_set in ErrorFinder.subsets(other_cols)]

                    # Find best summation
                    best_ratio = 0
                    best_sum = None
                    for subset in subsets:
                        sum = df_num[subset].sum(axis=1).values
                        target = df_num[header].values
                        # compare sum and target
                        bool = np.abs(target - sum) < tolerance
                        # make smart statistic that does not take zeros into account
                        non_zero_inds = np.abs(target - df_num[subset].max(axis=1).values) > tolerance
                        bool = bool[non_zero_inds]
                        ratio = np.sum(bool)/bool.size
                        if ratio > ErrorFinder.threshold and ratio >= best_ratio:
                            logger.info(str(subset.tolist()) + " sums up to " + header + " with ratio: " + str(ratio))
                            best_ratio = ratio
                            best_sum = sum
                            #if ratio == 1:
                            #    break
                    if best_ratio >= 0.95:
                        df_data[header] = best_sum
                        df_profiles[header] = 2
            dh.update_with_ind(dh_ind, df_data, df_profiles)
        return dh

    @staticmethod
    def subsets(s):
        for cardinality in range(2, len(s)+1):
            yield from combinations(s, cardinality)


class SumRowFinder:

    @staticmethod
    def detect_sum_row(dh, tolerance=1):
        for dh_ind, ds in enumerate(dh):
            df_data, df_profiles = ds.df_data, ds.df_profiles
            logger = logging.getLogger("data_cloud_logger")

            # find set of numeric cols
            df_num = TypeColExtracter.extract_num_cols(df_data, df_profiles)

            # Compare sum and last row
            sum = df_num.sum().values
            tail = df_num.tail(1).values[0] * 2

            bool_diff = sum-tail < tolerance
            sum_ratio = np.sum(bool_diff)/bool_diff.size
            # if its a sum row, kill it!
            if sum_ratio >= 0.5:
                df_data.drop(df_data.tail(1).index, inplace=True)
                df_profiles.drop(df_profiles.tail(1).index, inplace=True)
                logger.info("Dropped the last row, since it was a sum row")

            dh.update_with_ind(dh_ind, df_data, df_profiles)
        return dh


class CurrencyColGen:

    @staticmethod
    def generate_currency_col(dh):
        for dh_ind, df_data, df_profiles in dh.enumerate():
            # make new header
            header = str(df_data.columns.size + 1).zfill(pp.N_DIGITS_HEADER_PADDING) + ". Currency"
            #make th new column
            cur_col = np.array(["SEK" for i in range(df_data.index.size)])
            prof_col = np.ones(df_data.index.size)
            df_data[header] = cur_col
            df_profiles[header] = prof_col
            dh.update_with_ind(dh_ind, df_data, df_profiles)
        return dh
