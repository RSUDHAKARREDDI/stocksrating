file_list_config = {
    'latest_files': {
        'file_list': ['latest-results.csv'],
        'target_directory': 'datafiles/uploads',
        'table_name': 'latest_results',
        'mode':'replace',
        'file_pattern': None,
        'rename_to': None  # Added for consistency
    },
    'screeners': {
        'file_list': [
            'eps_pe_mscaps.csv', 'good_roe_roce_more_pe.csv',
            'good_pe_roe_roce_lcap.csv', 'good_pe_less_roe_roce.csv',
            'good_pe_roe_roce_all_good.csv', 'good_pe_roe_roce_altimate.csv',
            'less_public_holding.csv', 'power_bi_query.csv'
        ],
        'target_directory': 'datafiles/uploads',
        'table_name': 'screeners',
'mode':'replace',
        'file_pattern': None,
        'rename_to': None
    },
    'mc_technicals': {
        'file_list': ['mc_technicals.csv'],
        'target_directory': 'datafiles/uploads',
        'table_name': 'mc_technicals',
'mode':'replace',
        'file_pattern': None,
        'rename_to': None
    },
    'mstock_margin': {
        'file_list': ['mstock_margin.csv'],
        'target_directory': 'datafiles/uploads',
        'table_name': 'mstock_margin',
'mode':'replace',
        'file_pattern': None,
        'rename_to': None
    },
    'company_list': {
        'file_list': ['company_list.csv'],
        'target_directory': 'datafiles/others',
        'table_name': 'company_list',
    'mode':'replace',
        'file_pattern': None,
        'rename_to': None
    },
    'score_refactor': {
        'file_list': ['score_refactor.csv'],
        'target_directory': 'datafiles/score_refactor',
        'table_name': 'score_refactor',
'mode':'replace',
        'file_pattern': None,
        'rename_to': None
    },
    'bhav_copy': {
        'file_list': ['bhav_copy.csv'],
        'target_directory': 'datafiles/uploads',
        'table_name': 'bhav_copy',
        'mode':'replace',
        'file_pattern': 'sec_bhavdata_full_',
        'rename_to': 'bhav_copy.csv'
    },
    '52_wk_High_low': {
        'file_list': ['52_wk_High_low.csv'],
        'target_directory': 'datafiles/uploads',
        'table_name': '52_wk_high_low',
        'mode':'replace',
        'file_pattern': 'CM_52_wk_High_low_',
        'rename_to': '52_wk_High_low.csv' # Added .csv
    }
}