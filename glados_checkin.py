import requests
import os
import json
import time

# 配置信息
CHECKIN_URL = "https://glados.rocks/console/checkin"
TRAFFIC_URL = "https://glados.rocks/api/user/traffic"
SERVERCHAN_URL = "https://sctapi.ftqq.com/{}.send"

# 请求头模板
HEADERS_TEMPLATE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

def send_serverchan(sckey, title, content):
    """发送消息到Server酱"""
    if not sckey:
        print("未配置Server酱SCKEY，跳过推送")
        return
    
    try:
        url = SERVERCHAN_URL.format(sckey)
        data = {
            "title": title,
            "desp": content
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("Server酱推送成功")
        else:
            print(f"Server酱推送失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"Server酱推送异常: {str(e)}")

def get_traffic(cookie):
    """获取用户流量信息"""
    headers = HEADERS_TEMPLATE.copy()
    headers["Cookie"] = cookie
    headers["Accept"] = "application/json, text/plain, */*"
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "cors"
    
    try:
        response = requests.get(TRAFFIC_URL, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                traffic_data = data.get("data", {})
                used = traffic_data.get("used", 0) / (1024 ** 3)  # 转换为GB
                total = traffic_data.get("total", 0) / (1024 ** 3)  # 转换为GB
                return f"{used:.2f}GB / {total:.2f}GB"
        return "获取失败"
    except Exception as e:
        print(f"获取流量信息异常: {str(e)}")
        return "获取失败"

def checkin_account(cookie, account_index):
    """签到单个账号"""
    headers = HEADERS_TEMPLATE.copy()
    headers["Cookie"] = cookie
    
    try:
        # 先访问签到页面
        response = requests.get(CHECKIN_URL, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # 检查是否登录成功
            if "登录" in response.text or "Sign in" in response.text:
                return False, "Cookie已过期，请重新获取"
            
            # 获取流量信息
            traffic = get_traffic(cookie)
            
            # 这里Glados的签到是访问页面自动触发的
            # 如果页面包含"签到成功"或类似字样
            if "签到" in response.text or "Checkin" in response.text:
                return True, f"签到成功\n流量使用: {traffic}"
            else:
                return True, f"今日已签到\n流量使用: {traffic}"
        else:
            return False, f"请求失败，状态码: {response.status_code}"
    
    except Exception as e:
        return False, f"请求异常: {str(e)}"

def main():
    # 从环境变量获取配置
    cookies_str = os.environ.get("GLADOS_COOKIES", "")
    sckey = os.environ.get("SERVERCHAN_SCKEY", "")
    
    if not cookies_str:
        print("错误: 未配置GLADOS_COOKIES环境变量")
        send_serverchan(sckey, "Glados签到失败", "错误: 未配置GLADOS_COOKIES环境变量")
        return
    
    # 分割多账号Cookie (使用&&分隔)
    cookies = [cookie.strip() for cookie in cookies_str.split("&&") if cookie.strip()]
    
    success_count = 0
    fail_count = 0
    results = []
    
    print(f"共检测到 {len(cookies)} 个账号")
    
    for i, cookie in enumerate(cookies, 1):
        print(f"\n正在签到第 {i} 个账号...")
        success, message = checkin_account(cookie, i)
        
        if success:
            success_count += 1
            results.append(f"✅ 账号 {i}: {message}")
        else:
            fail_count += 1
            results.append(f"❌ 账号 {i}: {message}")
        
        # 账号之间添加延迟，避免请求过快
        if i < len(cookies):
            time.sleep(3)
    
    # 生成结果报告
    title = f"Glados签到结果: 成功{success_count}个，失败{fail_count}个"
    content = "\n\n".join(results)
    
    print("\n" + "="*50)
    print(title)
    print("="*50)
    print(content)
    
    # 推送结果到Server酱
    send_serverchan(sckey, title, content)

if __name__ == "__main__":
    main()
