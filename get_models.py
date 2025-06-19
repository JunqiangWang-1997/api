import os
import json
from bs4 import BeautifulSoup

def get_models_from_html(html_content):
    models_data = []
    soup = BeautifulSoup(html_content, 'lxml')

    # 查找所有的h2标签，它们通常代表模型类别
    categories = soup.find_all('h2')
    
    current_category = "未知类别"

    for h2_tag in categories:
        category_text = h2_tag.get_text(strip=True)
        if category_text:
            current_category = category_text.replace('<b>', '').replace('</b>', '') # 清理可能存在的<b>标签

        # 查找当前h2标签之后的所有table标签
        # 遍历h2标签的兄弟节点，直到遇到下一个h2标签或文档结束
        for sibling in h2_tag.find_next_siblings():
            if sibling.name == 'h2':
                break # 遇到下一个h2，停止处理当前类别
            
            if sibling.name == 'table':
                # 查找表格中的所有行
                rows = sibling.find_all('tr')
                
                # 尝试从表格的标题行中获取列索引
                header_row = rows[0] if rows else None
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                    model_col_index = -1
                    desc_col_index = -1
                    
                    # 尝试找到“模型”和“说明”列的索引
                    for i, header in enumerate(headers):
                        if "模型" in header:
                            model_col_index = i
                        if "说明" in header:
                            desc_col_index = i
                    
                    # 遍历数据行（跳过标题行）
                    for row in rows[1:]:
                        cols = row.find_all(['td', 'th'])
                        model_name = ""
                        description = ""

                        if model_col_index != -1 and len(cols) > model_col_index:
                            # 提取模型名称，通常在<a>标签内
                            a_tag = cols[model_col_index].find('a')
                            if a_tag and a_tag.get_text(strip=True):
                                model_name = a_tag.get_text(strip=True)
                            elif cols[model_col_index].get_text(strip=True):
                                # 如果没有a标签，直接取td/th的文本
                                model_name = cols[model_col_index].get_text(strip=True)
                                # 清理模型名称中的<b>标签和多余的文本
                                model_name = model_name.replace('<b>', '').replace('</b>', '').split('当前与')[0].strip()
                                # 移除括号内的内容，例如 (Beta 版本)
                                model_name = model_name.split('（')[0].strip()
                                
                        if desc_col_index != -1 and len(cols) > desc_col_index:
                            description = cols[desc_col_index].get_text(strip=True)
                            # 清理说明中的换行符和多余空格
                            description = ' '.join(description.split())

                        if model_name and model_name not in [m['name'] for m in models_data]:
                            models_data.append({
                                "name": model_name,
                                "category": current_category,
                                "description": description
                            })
    
    # 额外处理“旗舰模型”表格，因为它的结构可能不同
    # 查找“旗舰模型”的h2标签
    flagship_h2 = soup.find('h2', string=lambda text: text and '旗舰模型' in text)
    if flagship_h2:
        current_category = "旗舰模型"
        flagship_table = flagship_h2.find_next_sibling('table')
        if flagship_table:
            rows = flagship_table.find_all('tr')
            if len(rows) > 0:
                # 旗舰模型的名称在第二行开始的<td>中
                model_names_row = rows[0] # 假设模型名称在第一行
                cols = model_names_row.find_all(['td', 'th'])
                # 跳过第一个“旗舰模型”的td
                for i in range(1, len(cols)):
                    a_tag = cols[i].find('a')
                    if a_tag and a_tag.get_text(strip=True):
                        model_name = a_tag.get_text(strip=True)
                        # 尝试获取描述，假设在同一个td的<p>标签中
                        description_p = cols[i].find('p', class_=lambda x: x != 'jc')
                        description = description_p.get_text(strip=True) if description_p else ""
                        
                        if model_name and model_name not in [m['name'] for m in models_data]:
                            models_data.append({
                                "name": model_name,
                                "category": current_category,
                                "description": description
                            })
    
    return models_data

if __name__ == "__main__":
    html_file_path = "c:/Users/77424/Desktop/新建 文本文档.txt"
    
    if not os.path.exists(html_file_path):
        print(f"错误: 文件 '{html_file_path}' 不存在。请确保文件路径正确。")
    else:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        models = get_models_from_html(html_content)
        
        if models:
            print("\n--- 从HTML中抓取到的模型列表 ---")
            for model in models:
                print(f"- 名称: {model['name']}, 类别: {model['category']}, 描述: {model['description']}")
            
            # 将结果保存到 JSON 文件
            output_json_path = "qwen_analysis/models/scraped_models.json"
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(models, f, ensure_ascii=False, indent=4)
            print(f"\n模型数据已保存到 '{output_json_path}'")
        else:
            print("未从HTML中抓取到任何模型信息。")
