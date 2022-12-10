import xlrd


# pip3 install xlrd==1.2.0

def get_xlsx_contents(workbook_path):
    workbook = xlrd.open_workbook(workbook_path)
    worksheet = workbook.sheet_by_index(0)
    first_col = []
    for row in range(0, worksheet.nrows):
        v = worksheet.cell_value(row, 0)
        # if isinstance(v, float) or str(v).isnumeric():
        #     v = int(v)
        first_col.append(v)

    def get_xlsx_col_contents_single(col_num):
        elm_to_get = {}
        for row in range(1, worksheet.nrows):
            elm_to_get[first_col[row]] = set()
            v = str(worksheet.cell_value(row, col_num))
            if v != '':
                for single_range in v.split(','):
                    single_range = single_range.strip()
                    if single_range.isnumeric():
                        elm_to_get[first_col[row]].add(int(single_range) - 1)
                    else:
                        for i in range(int(single_range.split('-')[0]) - 1, int(single_range.split('-')[1])):
                            elm_to_get[first_col[row]].add(i)
            elm_to_get[first_col[row]] = list(elm_to_get[first_col[row]])
        print(elm_to_get)
        return elm_to_get

    def get_xlsx_col_contents_range(col_num):
        elm_to_get = {}
        for row in range(1, worksheet.nrows):
            elm_to_get[first_col[row]] = set()
            v = str(worksheet.cell_value(row, col_num))
            if v != '':
                for single_range in v.split(','):
                    single_range = single_range.strip()
                    elm_to_get[first_col[row]].add(
                        (int(single_range.split('-')[0]) - 1, int(single_range.split('-')[1]) - 1))
            elm_to_get[first_col[row]] = list(elm_to_get[first_col[row]])
        print(elm_to_get)
        return elm_to_get

    elm_to_remove = get_xlsx_col_contents_single(1)
    elm_to_reverse = get_xlsx_col_contents_range(2)
    elm_to_merge = get_xlsx_col_contents_range(3)
    elm_to_par = get_xlsx_col_contents_single(4)
    elm_to_vas = get_xlsx_col_contents_single(5)
    elm_to_add_bracket = get_xlsx_col_contents_single(6)
    return elm_to_remove, elm_to_reverse, elm_to_merge, elm_to_par, elm_to_vas, elm_to_add_bracket
