from python_back_end.triangle_formatting.header_finder import TriangleHeaderFinder
from python_back_end.triangle_formatting.sub_triangler import SubTriangler
from python_back_end.triangle_table_formatting.triangle_from_table_builder import TriangleFromTableBuilder
from python_back_end.triangle_formatting.triangle_utils import *
from python_back_end.triangle_formatting.hole_filler import StringFiller, DateFiller
from python_back_end.data_cleaning.cleaning_utils import *
from python_back_end.utilities.call_encapsulators import DataHolderCallEncapsulator
from python_back_end.triangle_formatting.triangle_stripper import TriangleStripper
from python_back_end.triangle_table_formatting.col_type_identifier import ColTypeIdentifier
from python_back_end.triangle_table_formatting.date_numifyer import DateNumifyer
from python_back_end.triangle_formatting.triangle_chopper import TriangleChopper
from python_back_end.triangle_table_formatting.dead_row_purger import DeadRowPurger

class TrianglePipeline:

    @staticmethod
    def triangle_pipeline_dh(dh, dhce=None, tri_type="single", n_outputs=1):
        """
        Performs a list of operations on an incoming DataHolder (dh)
        :param dh:
        :param dhce:
        :param tri_type:
        :param n_outputs:
        :return:
        """
        if dhce == None:
            dhce = DataHolderCallEncapsulator()
        # save original state
        #dh.create_memento()
        # Divide sheet in subunits
        dh = dhce.encapsulate_call(SheetPreProcessor.pre_strip, dh)
        # Merge some components again
        #dh = dhce.encapsulate_call(SheetPreProcessor.merge_components, dh)
        # Find the headers and remove them from the sheet
        dh, meta_dh = dhce.encapsulate_call(TriangleHeaderFinder.find_triangle_headers, dh, return_meta=True)

        # Check if year column is available in reasonable form
        dh = dhce.encapsulate_call(DateFiller.identify_and_gen_date_cols, dh, replace_col=False)

        # Fill periodically empty string cols
        dh = dhce.encapsulate_call(StringFiller.fill_hollow_str_cols, dh)

        # Chop triangles if needed
        dh = dhce.encapsulate_call(TriangleChopper.chop_triangles, dh, tri_type=tri_type)

        # try:
        new_dh, new_dh_dict = dhce.encapsulate_call(SubTriangler.make_standard_triangles, dh, meta_dh=meta_dh, tri_type=tri_type, n_outputs=n_outputs)
        # except NoSubTrianglesException as n:
        #     print(n)
        # Sort according to dates if needed
        #new_dh = dhce.encapsulate_call(DateSorter.sort_by_date, new_dh)
        # Strip unnecessary cols
        for key in new_dh_dict:
            new_dh_dict[key] = dhce.encapsulate_call(TriangleStripper.strip_triangles, new_dh_dict[key], tri_type=tri_type)
        return new_dh_dict, new_dh_dict[new_dh.name]

    @staticmethod
    def table_triangle_pipeline_dh(dh, dhce=None):
        """
            Performs a list of operations on an incoming DataHolder (dh)
            :param dh:
            :param dhce:
            :param tri_type:
            :param n_outputs:
            :return:
        """
        if dhce == None:
            dhce = DataHolderCallEncapsulator()

        # Pre strip
        dh = dhce.encapsulate_call(SheetPreProcessor.pre_strip, dh)

        dh, meta = dhce.encapsulate_call(HeaderFinder.find_headers, dh)

        # Check if year column is available in reasonable form
        dh = dhce.encapsulate_call(DateFiller.identify_and_gen_date_cols, dh, replace_col=False)

        #put dates in a
        dh, meta = dhce.encapsulate_call(DateNumifyer.numify_dates, dh)

        # Identify types
        dh = dhce.encapsulate_call(ColTypeIdentifier.identify_col_types, dh)

        dh = dhce.encapsulate_call(DeadRowPurger.purge_dead_rows, dh)

        dh = dhce.encapsulate_call(TriangleFromTableBuilder.build_triangle_from_table, dh)

        if dh.n == 0:
            raise NothingFoundInPipelineException(dh)

        return {dh.name: dh}, dh
