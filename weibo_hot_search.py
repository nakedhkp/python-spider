import requests
import json
import time
import random
from datetime import datetime
import pymysql
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WeiboHotSearchSpider:
    def __init__(self, interface_type: str = 'mobile'):
        """
        初始化爬虫
        :param interface_type: 'mobile' 或 'pc'，指定使用移动端还是PC端接口
        """
        self.interface_type = interface_type
        self.headers = self._get_headers()
        self.cookies = self._get_cookies()
        
        # 接口URL
        self.urls = {
            'mobile': 'https://weibo.com/ajax/side/hotSearch',
            'pc': 'https://s.weibo.com/top/summary'
        }
        
        # MySQL配置（需要根据实际情况修改）
        self.mysql_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'your_password',
            'database': 'weibo_hot_search',
            'charset': 'utf8mb4'
        }

    def _get_headers(self) -> Dict:
        """获取请求头"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://weibo.com/',
            'Origin': 'https://weibo.com',
        }

    def _get_cookies(self) -> Dict:
        """获取cookies（需要从浏览器中获取并更新）"""
        return {
            'SUB': '_2A25FECkxDeRhGeFH6lQR8S7IzjuIHXVmbCT5rDV8PUNbmtANLUj2kW9Ne_U69i99dP0dNnqTBRL2hvh3VNZB9XDz',
            'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9WW7lRgl',
            # 添加其他必要的cookies
        }

    def fetch_data(self) -> Optional[List[Dict]]:
        """
        获取热搜数据
        :return: 热搜数据列表
        """
        try:
            url = self.urls[self.interface_type]
            response = requests.get(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=10
            )
            response.raise_for_status()
            
            if self.interface_type == 'mobile':
                data = response.json()
                hot_searches = data.get('data', {}).get('realtime', [])
                return [{
                    'keyword': item.get('note'),
                    'hot': item.get('num'),
                    'rank': item.get('rank'),
                    'change': item.get('change'),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                } for item in hot_searches]
            else:
                # PC端接口解析逻辑（需要根据实际返回格式调整）
                pass
                
        except Exception as e:
            logging.error(f"获取数据失败: {str(e)}")
            return None

    def save_to_mysql(self, data: List[Dict]) -> bool:
        """
        保存数据到MySQL
        :param data: 热搜数据列表
        :return: 是否保存成功
        """
        try:
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            
            # 创建表（如果不存在）
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS hot_search (
                id INT AUTO_INCREMENT PRIMARY KEY,
                keyword VARCHAR(255),
                hot INT,
                rank INT,
                change_status VARCHAR(50),
                timestamp DATETIME
            )
            """
            cursor.execute(create_table_sql)
            
            # 插入数据
            insert_sql = """
            INSERT INTO hot_search (keyword, hot, rank, change_status, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            """
            for item in data:
                cursor.execute(insert_sql, (
                    item['keyword'],
                    item['hot'],
                    item['rank'],
                    item['change'],
                    item['timestamp']
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logging.error(f"保存到MySQL失败: {str(e)}")
            return False
            
        finally:
            if 'conn' in locals():
                conn.close()

    def save_to_txt(self, data: List[Dict], filename: str = 'hot_search.txt') -> bool:
        """
        保存数据到txt文件
        :param data: 热搜数据列表
        :param filename: 文件名
        :return: 是否保存成功
        """
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            logging.error(f"保存到txt失败: {str(e)}")
            return False

    def run(self, save_type: str = 'txt', interval: int = 300):
        """
        运行爬虫
        :param save_type: 保存类型，'txt' 或 'mysql'
        :param interval: 抓取间隔（秒）
        """
        while True:
            try:
                data = self.fetch_data()
                if data:
                    if save_type == 'txt':
                        self.save_to_txt(data)
                    else:
                        self.save_to_mysql(data)
                    logging.info(f"成功抓取并保存 {len(data)} 条热搜数据")
                
                # 随机延迟，避免固定间隔
                sleep_time = interval + random.randint(-30, 30)
                time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"运行出错: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再重试

if __name__ == '__main__':
    # 使用示例
    spider = WeiboHotSearchSpider(interface_type='mobile')
    spider.run(save_type='txt', interval=300) 