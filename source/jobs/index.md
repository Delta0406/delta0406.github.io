---
title: 大厂招聘看板  # 直接写你想显示的中文
layout: layout
---

<style>
    /* 保持你原有的样式，增加详情页微调 */
    #wordCloud { margin: 20px 0; text-align: center; line-height: 2; padding: 15px; background: rgba(0,0,0,0.02); border-radius: 12px; min-height: 50px; }
    .cloud-tag { display: inline-block; padding: 2px 10px; margin: 4px; border-radius: 15px; background: #f0f2f5; cursor: pointer; border: 1px solid #eee; transition: 0.2s; color: #444; }
    .cloud-tag:hover { background: #007bff; color: white !important; }
    
    /* 职位卡片改为详情折叠样式 */
    .job-card { border: 1px solid #f0f0f0; margin-bottom: 1rem; border-radius: 8px; background: #fff; border-left: 4px solid #007bff; overflow: hidden; }
    .job-card summary { padding: 1.2rem; cursor: pointer; list-style: none; outline: none; }
    .job-card summary::-webkit-details-marker { display: none; } /* 隐藏默认箭头 */
    
    .job-content { padding: 0 1.2rem 1.2rem 1.2rem; border-top: 1px dashed #eee; background: #fafafa; }
    .req-text { white-space: pre-wrap; font-size: 14px; color: #555; line-height: 1.6; margin-top: 10px; }
    .official-link { display: inline-block; margin-top: 15px; color: #007bff; text-decoration: none; font-weight: bold; }
    
    #jobSearch { width: 100%; padding: 12px 20px; border-radius: 25px; border: 1px solid #ddd; margin: 20px 0; outline: none; box-sizing: border-box; }
</style>

<div id="wordCloud">正在解析技术词云...</div>
<input type="text" id="jobSearch" placeholder="搜索职位名称、要求或技术栈...">
<div id="jobList">正在从云端获取大厂实时招聘信息...</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/jobs_data.json')
        .then(response => {
            if (!response.ok) throw new Error('网络响应错误');
            return response.json();
        })
        .then(data => {
            const listCont = document.getElementById('jobList');
            const cloudCont = document.getElementById('wordCloud');

            function render(filter = '') {
                const lowerFilter = filter.toLowerCase();
                
                // 1. 渲染词云
                cloudCont.innerHTML = data.cloud.map(tag => `
                    <span class="cloud-tag" style="font-size: ${Math.min(24, 13 + (tag.value * 0.5))}px" onclick="setSearch('${tag.name}')">
                        ${tag.name}
                    </span>
                `).join('');

                // 2. 增强搜索逻辑：同时搜索职位名和职位要求 (Requirement)
                const filtered = data.jobs.filter(j => 
                    j.RecruitPostName.toLowerCase().includes(lowerFilter) || 
                    (j.Requirement && j.Requirement.toLowerCase().includes(lowerFilter)) ||
                    j.company.toLowerCase().includes(lowerFilter)
                );
                
                // 3. 渲染职位列表 (使用 details 标签展示要求)
                listCont.innerHTML = filtered.map(j => `
                    <details class="job-card">
                        <summary>
                            <h3 style="display:inline; margin:0; color:#007bff; font-size:1.1rem;">${j.RecruitPostName}</h3>
                            <p style="margin:8px 0 0; font-size:13px; color:#666;">
                                <span style="background:#eef2ff;color:#46e;padding:2px 6px;border-radius:4px;font-weight:bold;">${j.company}</span>
                                📍 ${j.LocationName || '全国'} | 🕒 ${j.LastUpdateTime || '近期'} 
                                <span style="float:right; color:#999;">点击展开要求 ↓</span>
                            </p>
                        </summary>
                        <div class="job-content">
                            <h4 style="margin: 15px 0 5px 0; font-size:15px;">岗位要求：</h4>
                            <div class="req-text">${j.Requirement || '暂无详细要求描述'}</div>
                            <a href="${j.link}" target="_blank" class="official-link">🔗 查看官方招聘原文</a>
                        </div>
                    </details>
                `).join('');

                if(filtered.length === 0) {
                    listCont.innerHTML = "<p style='text-align:center; color:#999;'>没有找到相关的职位信息</p>";
                }
            }

            window.setSearch = function(val) {
                document.getElementById('jobSearch').value = val;
                render(val);
                window.scrollTo({ top: document.getElementById('jobSearch').offsetTop - 20, behavior: 'smooth' });
            };

            document.getElementById('jobSearch').oninput = (e) => render(e.target.value);
            render();
        })
        .catch(err => {
            console.error(err);
            document.getElementById('jobList').innerHTML = "数据加载失败，请检查 /api/jobs_data.json。";
        });
});
</script>