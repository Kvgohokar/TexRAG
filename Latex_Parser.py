##Functions
import json
import re
from pyparsing import Forward, Combine, SkipTo, Regex, Suppress, White, Located, nestedExpr, Or

#Equations
def extract_math_equations(latex_code):
    escaped_dollar = Regex(r'\\\$')
    math_content = Forward()
    math_content <<= Combine(SkipTo('$', ignore=escaped_dollar) | escaped_dollar)

    inline_math_mode = Suppress('$') + math_content.setResultsName('math_expr') + Suppress('$')
    display_math_mode = Suppress(r'\[') + SkipTo(r'\]').setResultsName('math_expr') + Suppress(r'\]')
    math_mode = Suppress(r'\begin{math}') + SkipTo(r'\end{math}').setResultsName('math_expr') + Suppress(r'\end{math}')
    display_math = Suppress(r'\begin{displaymath}') + SkipTo(r'\end{displaymath}').setResultsName('math_expr') + Suppress(r'\end{displaymath}')
    double_display_math_mode = Suppress(r'$$') + SkipTo(r'$$').setResultsName('math_expr') + Suppress(r'$$')
    equation_env = Suppress(r'\begin{equation}') + SkipTo(r'\end{equation}').setResultsName('equation') + Suppress(r'\end{equation}')
    equation_env_ = Suppress(r'\begin{equation*}') + SkipTo(r'\end{equation*}').setResultsName('equation') + Suppress(r'\end{equation*}')
    eqnarray_env = Suppress(r'\begin{eqnarray}') + SkipTo(r'\end{eqnarray}').setResultsName('eqnarray') + Suppress(r'\end{eqnarray}')
    eqnarray_env_ = Suppress(r'\begin{eqnarray*}') + SkipTo(r'\end{eqnarray*}').setResultsName('eqnarray') + Suppress(r'\end{eqnarray*}')
    aligned_env = Suppress(r'$$\begin{aligned}') + SkipTo(r'\end{aligned}$$').setResultsName('aligned') + Suppress(r'\end{aligned}$$')
    aligned_env_ = Suppress(r'\begin{aligned*}') + SkipTo(r'\end{aligned*}').setResultsName('aligned') + Suppress(r'\end{aligned*}')
    gathered_env = Suppress(r'\begin{gathered}') + SkipTo(r'\end{gathered}').setResultsName('gathered') + Suppress(r'\end{gathered}')
    gathered_env_ = Suppress(r'\begin{gathered*}') + SkipTo(r'\end{gathered*}').setResultsName('gathered') + Suppress(r'\end{gathered*}')
    array_env = Suppress(r'\begin{array}') + SkipTo(r'\end{array}').setResultsName('array') + Suppress(r'\end{array}')
    array_env_ = Suppress(r'\begin{array*}') + SkipTo(r'\end{array*}').setResultsName('array') + Suppress(r'\end{array*}')
    align_env = Suppress(r'\begin{align}') + SkipTo(r'\end{align}').setResultsName('align') + Suppress(r'\end{align}')
    align_env_ = Suppress(r'\begin{align*}') + SkipTo(r'\end{align*}').setResultsName('align') + Suppress(r'\end{align*}')

    whitespace = White().suppress()

    latex_parser = (double_display_math_mode
                    | display_math_mode
                    | display_math
                    | math_mode
                    | inline_math_mode
                    | equation_env
                    | equation_env_
                    | eqnarray_env
                    | eqnarray_env_
                    | aligned_env
                    | aligned_env_
                    | gathered_env
                    | gathered_env_
                    | array_env
                    | array_env_
                    | align_env
                    | align_env_
                    | whitespace)

    equations = []
    for result in latex_parser.scanString(latex_code):
        if result[0].get('math_expr'):
            equations.append(result[0].math_expr.strip())
        elif result[0].get('equation'):
            equations.append(result[0].equation.strip())
        elif result[0].get('eqnarray'):
            equations.append('\\begin{eqnarray}' + result[0].eqnarray.strip() + '\\end{eqnarray}')
        elif result[0].get('aligned'):
            equations.append('\\begin{aligned}' + result[0].aligned.strip() + '\\end{aligned}')
        elif result[0].get('gathered'):
            equations.append('\\begin{gathered}' + result[0].gathered.strip() + '\\end{gathered}')
        elif result[0].get('array'):
            equations.append('\\begin{array}' + result[0].array.strip() + '\\end{array}')
        elif result[0].get('align'):
            equations.append('\\begin{aligned}' + result[0].align.strip() + '\\end{aligned}')
    return equations

def latex_to_equations_json(latex_code):
    latex_code = re.sub(r'\\\\\$', 'dollar', latex_code)

    equations = extract_math_equations(latex_code)

    equations_dict = {}
    for i, eq in enumerate(equations):
        label_match = re.search(r'\\label\{([^}]*)\}', eq)
        tag_match = re.search(r'\\tag\{([^}]*)\}', eq)
        if label_match:
            key = label_match.group(1)
            value = re.sub(r'\\label\{[^}]*\}', '', eq)
            equations_dict[key] = value.strip()
        elif tag_match:
            key = tag_match.group(1)
            value = re.sub(r'\\tag\{[^}]*\}', '', eq)
            equations_dict[key] = value.strip()
        else:
            equations_dict[f'equation_{i+1}'] = eq

    # Convert the dictionary to JSON format
    equations_json = json.dumps(equations_dict, indent=4)
    return equations_json

###########################
#Tables

def extract_tables(latex_code):
    tabular_env = Suppress(r'\begin{tabular}') + Located(nestedExpr(opener=r'<<', closer=r'>>')).setResultsName('tabular') + Suppress(r'\end{tabular}')
    table_env = Suppress(r'\begin{table}') + Located(nestedExpr(opener=r'<<', closer=r'>>')).setResultsName('table') + Suppress(r'\end{table>')

    whitespace = White().suppress()

    latex_parser = (table_env | tabular_env | whitespace)
    tables = []
    for result, start, end in latex_parser.scanString(latex_code):
        caption = None
        label = None
        description = None
        content = []

        if result.get('tabular'):
            content = result.get('tabular', []).asList()[1]
            table_content = ['\\begin{tabular}'] + flatten_list(content) + ['\\end{tabular}']
            caption, label, description = find_caption_and_label(latex_code, start)
            table_name = create_table_name(caption, label, description)
            tables.append((table_name, table_content, start, end))

        elif result.get('table'):
            content = result.get('table', []).asList()[1]
            table_content = ['\\begin{table}'] + flatten_list(content) + ['\\end{table}']
            caption, label, description = find_caption_and_label(latex_code, start)
            table_name = create_table_name(caption, label, description)
            tables.append((table_name, table_content, start, end))

    return tables

def flatten_list(lst):
    flattened = []
    for item in lst:
        if isinstance(item, list):
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened

def find_caption_and_label(latex_code, start_pos):
    content = latex_code[start_pos:]
    if isinstance(start_pos, int):
        caption_match = re.search(r'\\caption\{(.*?)\}', content)
        label_match = re.search(r'\\label\{(.*?)\}', content)
        description_match = re.search(r'end{tabular}\n\\end{center}\s*\n\n(.*?)Table\s+\d+(\.\d+)?\s*:\s*(.*?)\n', content, re.DOTALL)

        caption = caption_match.group(1) if caption_match else None
        label = label_match.group(1) if label_match else None
        description = description_match.group(3) if description_match else None

        return caption, label, description
    else:
        return None, None, None

def create_table_name(caption, label, description):
    if caption and label and description:
        return f"{caption}_{label}_{description}"
    elif caption and label:
        return f"{caption}_{label}"
    elif label:
        return label
    elif caption:
        return caption
    elif description:
        return description
    else:
        return None  
        
def preprocess(latex_code):
    modified_latex_code = re.sub(r'\\begin\{tabular\}', r'\\begin{tabular}<<', latex_code)
    modified_latex_code = re.sub(r'\\end\{tabular\}', r'>>\\end{tabular}', modified_latex_code)
    modified_latex_code = re.sub(r'\\begin\{table\}', r'\\begin{table}<<', modified_latex_code)
    modified_latex_code = re.sub(r'\\end\{table\}', r'>>\\end{table}', modified_latex_code)
    return modified_latex_code

def extract_tables_dict(latex_code):
  test = preprocess(latex_code)
  tables = extract_tables(test)
  tables_dict = {}
  for i, (table_name, table, start_pos, end_pos) in enumerate(tables):
      key = table_name if table_name else f'table_{i+1}'
      tables_dict[key] = ' '.join(table)
  return tables_dict

def extract_rows(latex_code):
    begin_tabular_pattern = re.compile(r'\\begin\{tabular\}')
    end_tabular_pattern = re.compile(r'\\end\{tabular\}')
    begin_table_pattern = re.compile(r'\\begin\{table\}')
    end_table_pattern = re.compile(r'\\end\{table\}')
    hline_pattern = re.compile(r'\\hline')

    all_tables_dict = {}
    tables = extract_tables_dict(latex_code)
    
    for name, table in tables.items():
        table_content = re.sub(begin_tabular_pattern, '', table)
        table_content = re.sub(end_tabular_pattern, '', table_content)
        table_content = re.sub(begin_table_pattern, '', table_content)
        table_content = re.sub(end_table_pattern, '', table_content)
        table_content = re.sub(hline_pattern, '', table_content)

        # Find the first occurrence of \\ and count the number of & before it
        first_occurrence_idx = table_content.find('\\\\')
        column_count = table_content[:first_occurrence_idx].count('&') + 1

        # Extract column names
        column_names = [name for name in table_content[:first_occurrence_idx].split('&')]

        newline_idx = column_names[0].find('\n')
        brace_idx = column_names[0].find('}')
        hline_idx = column_names[0].find('\\hline')
        if newline_idx != -1 or brace_idx != -1 or hline_idx != -1:
          column_names[0] = column_names[0][max(newline_idx, brace_idx, hline_idx) + 1:]

        # Split the rest of the content by &
        rows_content = table_content[first_occurrence_idx+2:].split('&')

        #Split the nth count according to \\ and insert the split thing in that list
        indices_to_split = list(range(column_count - 1, len(rows_content)-column_count + 1, column_count-1))
        new_rows_content = rows_content.copy()

        offset = 0
        for i in indices_to_split:
            adjusted_index = i + offset
            new_two = new_rows_content[adjusted_index].split('\\\\')

            new_rows_content.insert(adjusted_index, new_two[0])
            new_rows_content.insert(adjusted_index + 1, new_two[1])
            new_rows_content.pop(adjusted_index + 2)
            offset += 1

        rows = [list(new_rows_content[i:i+column_count]) for i in range(0,len(new_rows_content),column_count)]
        row_names = []
        if column_names[0].isspace():
          row_names = [rows[i][0] for i in range(len(rows))]

        all_rows_dict = {}
        for i, rows in enumerate(rows):
          all_row_dict = dict(zip(column_names,rows))
          if row_names != []:
            all_rows_dict[row_names[i]] = all_row_dict
          else:
            all_rows_dict[f"row{i+1}"] = all_row_dict

        all_tables_dict[name] = all_rows_dict

    return all_tables_dict

###############################################################
# Images captions

def extract_images(latex_code):
    figure_env = Suppress(r'\begin{figure}') + SkipTo(r'\end{figure}').setResultsName('image') + Suppress(r'\end{figure}')
    image_env = Suppress(r'\begin{image}') + SkipTo(r'\end{image}').setResultsName('image') + Suppress(r'\end{image}')
    figure_env_star = Suppress(r'\begin{figure*}') + SkipTo(r'\end{figure*}').setResultsName('image') + Suppress(r'\end{figure*}')

    latex_parser = Or([figure_env, image_env, figure_env_star])

    images = []
    for result in latex_parser.scanString(latex_code):
        if result[0].get('image'):
            images.append(result[0].image.strip())
    return images

def extract_image_captions(latex_code):
    captions_dict = {}
    images = extract_images(latex_code)
    counter = len(images)
    caption_pattern = re.compile(r'\\caption\{(.+?)\}')
    label_pattern = re.compile(r'\\label\{(.+?)\}')
    caption_nest_label = re.compile(r'\\caption\{\\label\{([^}]*)\}(.+?)\}')

    for i, image in enumerate(images):
        figure_key = f"figure_{i+1}"
        captions_dict[figure_key] = {}
        caption_nest_matches = caption_nest_label.findall(image)
        if caption_nest_matches:
            for label, caption in caption_nest_matches:
                captions_dict[figure_key][label] = caption
        else:
            caption_matches = list(caption_pattern.finditer(image))
            for j, caption_match in enumerate(caption_matches):
                caption = caption_match.group(1)
                if j < len(caption_matches) - 1:
                    next_caption_start = caption_matches[j + 1].start()
                else:
                    next_caption_start = len(image)
                label_match = label_pattern.search(image, caption_match.end(), next_caption_start)
                if label_match:
                    label = label_match.group(1)
                    captions_dict[figure_key][label] = caption
                else:
                    captions_dict[figure_key][f"subfig_{j+1}"] = caption

    figure_pattern = re.compile(
        r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}\s*\\end\{center\}\s*Figure\s*([^\n]+)\n',
        re.DOTALL
    )
    figure_matches = figure_pattern.finditer(latex_code)
    for match in figure_matches:
        graphics = match.group(1)
        figure_sentence = match.group(2).strip()
        captions_dict[graphics] = figure_sentence

    graphics_pattern = re.compile(r'\\includegraphics(?:\[.*?\])?\{(.+?)\}')
    include_graphics_matches = graphics_pattern.findall(latex_code)
    for match in include_graphics_matches:
        if match not in captions_dict.keys() and match not in " ".join(images):
            counter += 1
            captions_dict[f'figure_{counter}'] = match

    captions_dict = json.dumps(captions_dict, indent=4)
    return captions_dict

#Extract title, author name, date 
def extract_content(latex_code):
    pattern = r'\\begin\{document\}(.*?)\\end\{document\}'
    
    match = re.search(pattern, latex_code, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return latex_code  

def extract_title(latex_code):
    patterns = {
        'title': r'\\title\{([^}]*)\}',
        'author': r'\\author\{([^}]*)\}',
        'date': r'\\date\{([^}]*)\}'
    }

    results = {}

    for key, pattern in patterns.items():
        match = re.search(pattern, latex_code)
        results[key] = match.group(1) if match else ''

    return results

def create_json_object(latex_code):
    # Extract the title, author, and date
    commands = extract_title(latex_code)
    
    # Extract content between \begin{document} and \end{document}
    document_content = extract_content(latex_code)
    
    equations_json = latex_to_equations_json(document_content)
    rows_dict = extract_rows(document_content)
    image_dict = extract_image_captions(document_content)

    json_object = {
        "Title": commands['title'],
        "Author": commands['author'],
        "Date": commands['date'],
        "Content": document_content,
        "Equations": equations_json,
        "Tables": rows_dict,
        "Image Captions": image_dict
    }
    
    return json_object

