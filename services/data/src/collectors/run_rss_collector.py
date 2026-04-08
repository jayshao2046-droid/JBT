import os

from services.data.src.collectors.rss_collector import RSSCollector

if __name__ == '__main__':
    # 代理环境变量，确保境外源可访问
    proxy_url = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy') or 'http://127.0.0.1:7890'
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url

    collector = RSSCollector()
    records = collector.collect()
    # symbol/data_type 约定为 'rss_news'，与原有落盘一致
    collector.save(symbol='rss_news', records=records, data_type='rss_news')
    print(f"[INFO] RSS采集完成，采集记录数: {len(records)}，已落盘至 parquet/news_rss/")
