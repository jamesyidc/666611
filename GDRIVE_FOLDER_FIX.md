# Google Drive 监控修复报告

## 问题描述
用户反馈：**没有找到最新一天的子文件夹id**

## 问题原因

配置文件 `daily_folder_config.json` 中的日期是旧日期（2025-12-25），但系统日期已经变为新的一天（2025-12-26）。

### 具体原因
1. **日期不匹配**: 配置文件 `current_date: 2025-12-25` vs 系统日期 `2025-12-26`
2. **文件夹ID过期**: 旧的文件夹ID `1ncQpa9fGmroMWbXM4U7gbbWDtJT5xlWX` 是昨天的
3. **自动更新未触发**: 系统有11分钟超时自动恢复机制，但需要等待触发

### 错误日志
```
⚠️  警告：配置文件日期不匹配！
⚠️  配置文件日期: 2025-12-25
⚠️  当前系统日期: 2025-12-26
⚠️  使用默认文件夹ID: 1jFGGlGP5KEVhAxpCNxFIYEFI5-cDOBjM
⚠️  请更新 config.json 文件中的 current_date 和 folder_id
```

## 解决方案

### 手动更新配置文件

执行以下Python脚本手动查找并更新今天的文件夹ID：

```python
import requests
import re
from bs4 import BeautifulSoup
import json
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
CONFIG_FILE = "/home/user/webapp/daily_folder_config.json"
ROOT_FOLDER_ODD = "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV"  # 单数日期父文件夹
ROOT_FOLDER_EVEN = "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV"  # 双数日期父文件夹

today = datetime.now(BEIJING_TZ)
today_str = today.strftime('%Y-%m-%d')
day_of_month = today.day
is_odd_day = day_of_month % 2 == 1

# 选择父文件夹
root_folder_id = ROOT_FOLDER_ODD if is_odd_day else ROOT_FOLDER_EVEN

# 访问父文件夹查找今天的子文件夹
url = f"https://drive.google.com/embeddedfolderview?id={root_folder_id}"
response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.text, 'html.parser')

all_links = soup.find_all('a', href=True)
today_folder_id = None

for link in all_links:
    href = link.get('href', '')
    foldername = link.get_text(strip=True)
    
    if foldername == today_str:
        if '/folders/' in href:
            match = re.search(r'/folders/([a-zA-Z0-9_-]+)', href)
            if match:
                today_folder_id = match.group(1)
                break

if today_folder_id:
    config = {
        'root_folder_odd': ROOT_FOLDER_ODD,
        'root_folder_even': ROOT_FOLDER_EVEN,
        'current_date': today_str,
        'folder_id': today_folder_id,
        'parent_folder_id': root_folder_id,
        'updated_at': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S'),
        'update_reason': '手动更新新一天文件夹',
        'folder_name': today_str,
        'auto_updated': True
    }
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
```

### 修复结果

**修复前配置**:
```json
{
  "current_date": "2025-12-25",
  "folder_id": "1ncQpa9fGmroMWbXM4U7gbbWDtJT5xlWX"
}
```

**修复后配置**:
```json
{
  "current_date": "2025-12-26",
  "folder_id": "1jgqcidqq0PwA-2-AtHH6fM87Cuh3b99J",
  "parent_folder_id": "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV",
  "updated_at": "2025-12-26 00:41:06",
  "folder_name": "2025-12-26"
}
```

## 验证结果

### 重启后日志
```
[2025-12-26 00:41:15] 🔍 步骤4: 最新文件名 = 2025-12-26_0039.txt
[2025-12-26 00:41:16] 🆕 检测到新的TXT文件！
[2025-12-26 00:41:16] 📄 文件信息:
   最新文件名: 2025-12-26_0039.txt
   数据时间戳: 2025-12-26 00:39:36
[2025-12-26 00:41:16] ✅ 数据提取成功！
```

### 检测状态
- ✅ 今天日期: 2025-12-26
- ✅ 今天文件夹ID: `1jgqcidqq0PwA-2-AtHH6fM87Cuh3b99J`
- ✅ 父文件夹: `1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV` (双数日期文件夹)
- ✅ 最新TXT文件: `2025-12-26_0039.txt`
- ✅ 数据提取成功
- ✅ 监控正常运行

## 自动恢复机制

系统内置了11分钟超时自动恢复机制：

```python
def get_root_folder_id_and_create_today_folder():
    """
    11分钟超时恢复机制:
    1. 重新获取根文件夹ID (父文件夹)
    2. 在根文件夹下创建/查找今天日期的文件夹
    3. 更新配置文件
    4. 返回新的文件夹ID
    """
```

**触发条件**: 当检测到11分钟内没有新文件时，自动触发

**处理流程**:
1. 访问父文件夹（根据日期选择单数/双数）
2. 查找今天日期的子文件夹（如 `2025-12-26`）
3. 更新配置文件
4. 继续正常监控

## 预防措施

### 每日0点自动更新
建议添加定时任务，在每天0点自动更新文件夹ID：

```bash
# 添加到crontab
0 0 * * * cd /home/user/webapp && python3 update_daily_folder.py
```

### 监控配置日期
添加日期检查，当发现日期不匹配时立即更新：

```python
def check_and_update_folder_daily():
    today = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    if config.get('current_date') != today:
        # 立即触发更新
        get_root_folder_id_and_create_today_folder()
```

## 文件结构

```
/home/user/webapp/
├── gdrive_final_detector.py          # 主检测脚本
├── daily_folder_config.json          # 每日文件夹配置
└── crypto_data.db                    # 数据库
```

## 配置文件说明

### 字段说明
- `current_date`: 当前监控日期（格式：YYYY-MM-DD）
- `folder_id`: 今天的Google Drive文件夹ID
- `parent_folder_id`: 父文件夹ID（单数/双数日期文件夹）
- `root_folder_odd`: 单数日期父文件夹ID
- `root_folder_even`: 双数日期父文件夹ID
- `updated_at`: 最后更新时间
- `folder_name`: 文件夹名称（同current_date）
- `auto_updated`: 是否自动更新

### 父文件夹规则
- **单数日期** (1, 3, 5, 7, 9, 11, 13, ...): 使用 `root_folder_odd`
- **双数日期** (2, 4, 6, 8, 10, 12, 14, ...): 使用 `root_folder_even`

## 状态确认

✅ **问题已完全解决**

- 配置文件已更新到今天（2025-12-26）
- Google Drive监控正常运行
- 能够检测到今天的新文件
- 数据提取和导入功能正常

---

**修复时间**: 2025-12-26 00:41:06  
**监控状态**: ✅ 正常运行  
**下次检查**: 每30秒自动检测
