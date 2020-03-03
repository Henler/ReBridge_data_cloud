from python_back_end.program_settings import PROGRAM_STRINGS as ps
class TriangleTemplater:

    @staticmethod
    def get_single_loss_triangle_template():
        single_list = [{    'headers': ["Date of loss", "Loss id", "Unit"],
                            'categories':  {
                    ps.CAT_PAID_NAME: {'type': 'independent', 'from': []},
                    ps.CAT_RESERVED_NAME: {'type': 'independent', 'from': []},
                    ps.CAT_INCURRED_NAME: {'type': 'sum', 'from': ['Claim - Paid', 'Claim - Reserved']}},
                            'currency': None,
                            'group_id': 0,
                            'type': "single",
                            'immutable_headers': ("Date of loss", "Loss id", "Unit")}]

        return single_list

    @staticmethod
    def get_aggregate_loss_triangle_template(outputFormats):
        aggregated_list = []

        if 'Claims' in outputFormats:
            aggregated_list.append({    
                'headers': ["Year", "Unit"],
                'categories': {
                    ps.CAT_PAID_NAME: {'type': 'independent', 'from': []},
                    ps.CAT_RESERVED_NAME: {'type': 'independent', 'from': []},
                    ps.CAT_INCURRED_NAME: {'type': 'sum', 'from': ['Claim - Paid', 'Claim - Reserved']}},
                'currency': None,
                'group_id': 0,
                'type': "aggregate",
                'immutable_headers': ("Year", "Unit")})

        if 'Premiums' in outputFormats:
            aggregated_list.append({   
                'headers': ["Year", "Unit"],
                'categories': {
                    ps.CAT_PREMIUM_NAME: {'type': 'independent', 'from': []},},
                'currency': None,
                'group_id': 0,
                'type': "aggregate",
                'immutable_headers': ("Year", "Unit")})

        return aggregated_list

    @staticmethod
    def create_triangle_template_with_group_ids(triangle_templates, nmbr_of_groups):
        triangle_template_group_id = []
        if nmbr_of_groups <= 0:
            triangle_template_group_id = triangle_templates
        else:
            for group_index in range(nmbr_of_groups):
                for template in triangle_templates:
                    triangle_copy = template.copy()
                    triangle_copy['group_id'] = group_index
                    triangle_template_group_id.append(triangle_copy)

        return triangle_template_group_id