import numpy as np
import re
import pandas as pd
from python_back_end.program_settings import PROGRAM_PARAMETERS as pp
from skimage.measure import label
import sys


def safe_round(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            try:
                matrix[i][j] = np.around(matrix[i][j])
            except:
                pass
    return matrix


def mad(array):
    devs = np.abs(np.mean(array) - array)
    return np.mean(devs)


def excel_compatible_sheet_name(sheet_name):
    forbidden_list = ["\\", "/", "*", "[", "]", ":", "?"]
    for forbidden in forbidden_list:
        sheet_name = sheet_name.replace(forbidden, "")
    sheet_name = sheet_name[0:25].strip()
    return sheet_name


def desc_ind(in_list, length, strict=True):
    if len(in_list) == 0:
        return 0
    past = in_list[0]
    index = 0
    for i in range(1, length):
        if strict:
            if past > in_list[i]:
                index += 1
        else:
            if past >= in_list[i]:
                index += 1
        past = in_list[i]
    return index/length


def ascend_ind(in_list, length, strict=True):
    assert isinstance(in_list, np.ndarray)
    if len(in_list) == 0:
        return 0
    turned = - in_list
    return desc_ind(turned, length, strict=strict)


def strict_index(int_list, strict=True):

    int_list = np.array(int_list)
    length = len(int_list)
    desc = desc_ind(int_list, length, strict=strict)
    asc = ascend_ind(int_list, length, strict=strict)

    return max(desc, asc)


def longest_numeral(input):
    numeral_list = re.findall(r'\d+', str(input))
    if len(numeral_list) != 0:
        return int(max(numeral_list, key=len))
    else:
        return 0


def right_merge_df_list(df_data_list):
    col_set = {str(x) for df in df_data_list for x in df.columns}
    ind_set = {x for df in df_data_list for x in df.index}
    merged = pd.DataFrame(columns=sorted(col_set), index=sorted(ind_set))

    for df in df_data_list:
       merged.loc[df.index, [str(x) for x in df.columns]] = df.values
    return merged


class ExhaustiveSubsetMaker:

    @staticmethod
    def sub_sets(sset):
        return ExhaustiveSubsetMaker.subsetsRecur([], sorted(sset))

    @staticmethod
    def subsetsRecur(current, sset):
        if sset:
            return ExhaustiveSubsetMaker.subsetsRecur(current, sset[1:]) + ExhaustiveSubsetMaker.subsetsRecur(current + [sset[0]], sset[1:])
        return [current]


def sum_unique(headers, values):
    unique, inverse = np.unique(headers, return_inverse=True)
    summed_inverse = np.array([np.sum(values[inverse == i]) for i in range(np.max(inverse) + 1)])
    order = np.argsort(unique)
    unique = unique[order]
    summed_inverse = summed_inverse[order]

    #print(unique, summed_inverse)
    #sys.exit(1)
    return unique, summed_inverse


def equals_recursively(inp1, inp2):
    if isinstance(inp1, list) and isinstance(inp2, list):
        if len(inp1) != len(inp2):
            return False
        bools = [equals_recursively(el1, el2) for el1, el2 in zip(inp1, inp2)]
        return all(bools)
    elif isinstance(inp1, dict) and isinstance(inp2, dict):
        if len(inp1) != len(inp2):
            return False
        sorted_zip = zip(sorted(inp1), sorted(inp2))
        bools = [el1 == el2 for el1, el2 in sorted_zip]
        sorted_zip = zip(sorted(inp1), sorted(inp2))
        bools += [equals_recursively(inp1[el1], inp2[el2]) for el1, el2 in sorted_zip]
        return all(bools)
    else:
        return inp1 == inp2

def general_adjacent(num_col_names):
    positions = np.array([int(el[0:pp.N_DIGITS_HEADER_PADDING]) for el in num_col_names])
    # Get longest consecutive sequence
    adj_seq_list = []
    for i in range(1, pp.MAX_NUM_HORIZONTAL_CHOPS + 1):
        adj_seq_list.append(positions[1:] - positions[0:-1] - i)
    zero_rows = np.sum(np.array(adj_seq_list) == 0, axis=1)
    adj_seq = np.array(list(adj_seq_list[np.argmax(zero_rows)]) + [1])
    adj_seq = adj_seq * adj_seq[range(-1, len(adj_seq) - 1)]
    components = label(adj_seq == 0)
    unique, counts = np.unique(components, return_counts=True)
    biggest_label = unique[np.argmax(counts)]

    adj_headers = num_col_names[components == biggest_label]
    return adj_headers
