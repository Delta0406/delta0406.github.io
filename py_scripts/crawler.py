import os
import json
import time
import requests
import re
import jieba
from collections import Counter


KEYWORDS_LIST = ["agent", "后台", "后端", "AI"]


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Referer": "https://careers.tencent.com/jobdesc.html"
}


def get_tencent_jobs_single_keyword(keyword, all_jobs_container, category_id="40001001,40001005"):
    """
    传入 all_jobs_container (字典)，根据 PostId 去重并追加数据
    """
    print(f"正在抓取腾讯关键词: {keyword}...")
    list_url = "https://careers.tencent.com/tencentcareer/api/post/Query"
    detail_url = "https://careers.tencent.com/tencentcareer/api/post/ByPostId"
    
    params = {
        "pageIndex": 1, 
        "pageSize": 50, 
        "language": "zh-cn", 
        "area": "cn",
        "keyword": keyword,
        "categoryId": category_id
    }
    
    try:
        res = requests.get(list_url, params=params, headers=HEADERS, timeout=10).json()
        posts = res.get('Data', {}).get('Posts', [])
        
        for p in posts:
            pid = p.get('PostId')
            # 跨公司/跨关键词去重核心逻辑
            if pid not in all_jobs_container:
                # 请求详情接口获取真正的 Requirement (截图中的 ByPostId 接口)
                detail_params = {
                    "timestamp": int(time.time() * 1000),
                    "postId": pid,
                    "language": "zh-cn"
                }
                try:
                    d_res = requests.get(detail_url, params=detail_params, headers=HEADERS, timeout=10).json()
                    d_data = d_res.get('Data', {})
                    
                    # 补全关键信息
                    p['company'] = '腾讯'
                    p['link'] = f"https://careers.tencent.com/jobdesc.html?postId={pid}"
                    p['Requirement'] = d_data.get('Requirement', "")    # 岗位要求
                    p['Responsibility'] = d_data.get('Responsibility', "") # 岗位职责
                    p['RecruitPostName'] = p.get('RecruitPostName', '未知职位')
                    
                    # 写入传入的全局容器
                    all_jobs_container[pid] = p
                    
                    # 详情抓取频率控制
                    time.sleep(0.2)
                except Exception as detail_e:
                    print(f"详情抓取失败 ID {pid}: {detail_e}")
                
    except Exception as e:
        print(f"关键词 {keyword} 列表抓取失败: {e}")


def get_tencent_jobs_all_keywords(all_jobs_container, keywords_list):
    """
    调度函数：遍历关键词列表，共用外部传入的 all_jobs_container
    """

    for kw in keywords_list:
        get_tencent_jobs_single_keyword(kw, all_jobs_container)
        # 关键词间歇，防止被封
        time.sleep(1)


def generate_word_cloud(jobs_list):
    """
    针对中英混合 JD 优化的关键词提取
    """
    full_text = ""
    for job in jobs_list:
        # 拼接标题与岗位要求
        full_text += f"{job.get('RecruitPostName', '')} {job.get('Requirement', '')} "

    # 1. 提取所有英文术语 (正则匹配：保留连续的字母，如 Python, LLM)
    english_words = re.findall(r'[a-zA-Z]{2,}', full_text) # 过滤掉单字母如 'a', 's'
    english_words = [w.upper() for w in english_words] # 统一转大写方便统计

    # 2. 提取中文关键词 (清理干扰字符后用 jieba)
    chinese_part = re.sub(r'[^\u4e00-\u9fa5]', ' ', full_text)
    jieba_words = jieba.cut(chinese_part)
    
    # 3. 综合过滤与统计
    stop_words = {'负责', '团队', '参与', '要求', '工作', '相关', '具有', '进行', '提供', '协作', '能力', 
                '优先', '岗位', '经验', '熟练', '以及', '完成', '本科', '以上', '学历', '专业', '腾讯',
                '开发', '熟悉', '系统', '模型', '优化', '应用', '沟通', '以上学历', '问题', '能够',
                '了解', '训练', '设计', '熟悉掌握', '语言', '研发', '精通', '框架', '良好', '算法',
                '后台', '分析', '编程', '工程师', '具备', '理解', '优秀', '项目', '方向', '至少', '游戏',
                '独立', '技术', '常用', '计算机相关', '使用', '计算机', '学习', '基础', '熟练掌握', '推理',
                '原理', '架构', '服务', '数据', '性能', '精神', '业务', '复杂', '一种', '平台', '意识',
                '工程', '解决', '合作', '深入', '责任心'}
    
    # 合并中英文结果
    final_word_list = []
    
    # 处理中文分词结果
    for w in jieba_words:
        if len(w) > 1 and w not in stop_words:
            final_word_list.append(w)
            
    # 加入英文术语
    for ew in english_words:
        if ew not in stop_words:
            final_word_list.append(ew)

    word_counts = Counter(final_word_list)
    
    # 返回前 30 个高频词
    return [{"name": name, "value": count} for name, count in word_counts.most_common(30)]

# --- 5. 主程序入口 ---
if __name__ == "__main__":
    # 实例化一个空的聚合池
    all_data_pool = {} 
    
    # 抓取腾讯全量关键词
    get_tencent_jobs_all_keywords(all_data_pool, KEYWORDS_LIST)
    
    # 转换为列表用于统计和词云
    final_jobs_list = list(all_data_pool.values())
    
    # 基于全量 Requirement 生成词云数据
    cloud_data = generate_word_cloud(final_jobs_list)
    
    # 统一存储为 JSON
    output_path = 'source/api/jobs_data.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = {
        "jobs": final_jobs_list,
        "cloud": cloud_data,
        "stats": {
            "total": len(final_jobs_list),
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"数据处理完成！聚合了 {len(final_jobs_list)} 个岗位，已更新至 {output_path}")