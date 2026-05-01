#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄小说下载器
适用于Termux环境
"""

import json
import urllib.request
import urllib.error
import os
import time
import sys
import re

# API配置
BASE_URL = "https://oiapi.net/api/FqRead"
API_KEY = "oiapi-b27b0c8d-8984-7cd0-ecaf-0c209ad109d2"

# 请求重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2

# 超时配置
TIMEOUT = 30


def clean_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r"[\/\\\:\*\?\"\<\>\|]", "_", name)


def api_request(url_params):
    """
    发送API请求，带重试机制（静默重试，不输出过程信息）
    """
    url = f"{BASE_URL}?{url_params}&key={API_KEY}"
    
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except urllib.error.URLError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise Exception(f"API请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("API返回的数据格式错误")
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise Exception(f"请求失败: {str(e)}")


def get_book_info(book_id):
    """获取书籍信息"""
    try:
        result = api_request(f"method=ids&id={book_id}")
        if result.get('code') == 1:
            return result['data']
        else:
            raise Exception(f"获取书籍信息失败: {result.get('message', '未知错误')}")
    except Exception as e:
        raise Exception(f"获取书籍信息错误: {str(e)}")


def get_chapter_list(book_id):
    """获取章节列表"""
    try:
        result = api_request(f"method=chapters&id={book_id}")
        if result.get('code') == 1:
            return result['data']
        else:
            raise Exception(f"获取章节列表失败: {result.get('message', '未知错误')}")
    except Exception as e:
        raise Exception(f"获取章节列表错误: {str(e)}")


def get_chapter_content(book_id, chapter_id):
    """获取单个章节内容"""
    try:
        result = api_request(f"method=chapter&id={book_id}&chapter={chapter_id}")
        if result.get('code') == 1:
            return result['data']
        else:
            raise Exception(f"获取章节内容失败: {result.get('message', '未知错误')}")
    except Exception as e:
        raise Exception(f"获取章节内容错误: {str(e)}")


def get_chapter_contents_batch(book_id, start_index, end_index):
    """批量获取章节内容"""
    chapter_range = f"{start_index}-{end_index}"
    try:
        result = api_request(f"method=chapter&id={book_id}&chapter={chapter_range}")
        if result.get('code') == 1:
            return result['data']
        else:
            raise Exception(f"批量获取章节内容失败: {result.get('message', '未知错误')}")
    except Exception as e:
        raise Exception(f"批量获取章节内容错误: {str(e)}")


def print_progress(current, total, final=False):
    """打印进度条"""
    percent = (current / total) * 100
    bar_length = 30
    filled = int(bar_length * current // total)
    bar = '█' * filled + '-' * (bar_length - filled)
    
    if final:
        sys.stdout.write(f'\r[{bar}] {percent:.1f}% {current}/{total} 下载完成\n')
    else:
        sys.stdout.write(f'\r[{bar}] {percent:.1f}% 正在下载{current}/{total}')
    sys.stdout.flush()


def clean_content(content):
    """清理章节内容，去掉HTML标签"""
    content = content.replace('</p><p>', '\n')
    content = content.replace('<p>', '')
    content = content.replace('</p>', '\n')
    content = re.sub(re.compile('<.*?>'), '', content)
    content = re.sub(r'\n+', '\n', content).strip()
    return content


def download_novel(book_id):
    """
    下载小说
    """
    print(f"\n获取书籍信息...")
    try:
        book_info = get_book_info(book_id)
        book_title = book_info['title']
        author = book_info['author']
        intro = book_info.get('docs', '').replace('\n', ' ')

        print(f"  书名: {book_title}")
        print(f"  作者: {author}")
        print(f"  简介: {intro[:100]}{'...' if len(intro) > 100 else ''}")

        # 获取章节列表
        chapters_data = get_chapter_list(book_id)

        # 展平章节列表（处理卷）
        chapters = []
        for volume in chapters_data:
            if isinstance(volume, list):
                chapters.extend(volume)
            elif isinstance(volume, dict):
                chapters.append(volume)

        total_chapters = len(chapters)

        # 准备保存
        safe_title = clean_filename(book_title)
        output_dir = os.path.join("/storage/emulated/0/Download", "novels")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{safe_title}.txt")

        print(f"\n开始下载...")

        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入书籍基本信息
            f.write(f"{book_title}\n")
            f.write(f"作者: {author}\n")
            f.write(f"简介:\n{intro}\n\n")

            BATCH_SIZE = 30
            for start in range(1, total_chapters + 1, BATCH_SIZE):
                end = min(start + BATCH_SIZE - 1, total_chapters)
                try:
                    batch_data = get_chapter_contents_batch(book_id, start, end)
                except Exception as e:
                    print(f"批量下载失败: {str(e)}")
                    for chap_idx in range(start, end + 1):
                        print_progress(chap_idx, total_chapters, f"第{chap_idx}章（跳过）")
                        f.write(f"第{chap_idx}章\n\n[下载失败]\n\n")
                    continue

                # 将返回列表转为字典，键为章节号
                chapter_dict = {}
                for item in batch_data:
                    chapter_num = item.get('chapter')
                    if chapter_num is not None:
                        chapter_dict[int(chapter_num)] = item

                for chap_idx in range(start, end + 1):
                    chapter_info = chapter_dict.get(chap_idx)
                    original_chapter = next((ch for ch in chapters if ch.get('index') == chap_idx), None)
                    title = original_chapter['title'] if original_chapter else chapter_info.get('chapter_title', f'第{chap_idx}章')

                    # 更新进度条
                    print_progress(chap_idx, total_chapters)

                    if chapter_info:
                        content = chapter_info.get('content', '')
                        content = clean_content(content)
                        if content.lstrip().startswith(title):
                            content = content.lstrip()[len(title):].strip()
                        f.write(f"{title}\n{content}\n\n")
                    else:
                        f.write(f"{title}\n[内容缺失]\n\n")

            # 全部完成
            print_progress(total_chapters, total_chapters, final=True)
            print(f"\n已保存到: {output_file}")

    except Exception as e:
        print(f"\n下载失败: {str(e)}")
        return False

    return True


def main():
    """主函数"""
    print("=" * 60)
    print("fq v3")
    print("桀桀桀桀桀")
    print("=" * 60)
    
    # 获取书籍ID
    book_id = input("\n请输入book id: ").strip()
    
    if not book_id:
        print("书籍ID不能为空")
        return
    
    # 开始下载
    download_novel(book_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断操作")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")