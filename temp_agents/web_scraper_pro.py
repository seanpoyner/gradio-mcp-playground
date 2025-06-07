import gradio as gr
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import os
from urllib.parse import urljoin, urlparse
from datetime import datetime

class WebScraperAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = []
        
    def scrape_advanced(self, url, content_type, custom_selector="", max_items=50):
        """Advanced web scraping with multiple extraction modes"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            results = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if content_type == "Article Text":
                # Extract main article content
                article_selectors = ['article', '.article', '#article', '.content', '.post-content', 'main']
                content = ""
                
                for selector in article_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = elements[0].get_text(strip=True, separator='\n')
                        break
                
                if not content:
                    # Fallback to all paragraphs
                    paragraphs = soup.find_all('p')
                    content = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
                
                results.append({
                    "type": "Article",
                    "url": url,
                    "content": content[:2000] + "..." if len(content) > 2000 else content,
                    "timestamp": timestamp
                })
                
            elif content_type == "All Links":
                links = soup.find_all('a', href=True)
                for link in links[:max_items]:
                    href = link['href']
                    text = link.get_text(strip=True)
                    if text and href:
                        full_url = urljoin(base_url, href) if not href.startswith('http') else href
                        results.append({
                            "type": "Link",
                            "text": text,
                            "url": full_url,
                            "timestamp": timestamp
                        })
                        
            elif content_type == "Images":
                images = soup.find_all('img', src=True)
                for img in images[:max_items]:
                    src = img['src']
                    alt = img.get('alt', 'No alt text')
                    title = img.get('title', '')
                    full_src = urljoin(base_url, src) if not src.startswith('http') else src
                    results.append({
                        "type": "Image", 
                        "alt": alt,
                        "title": title,
                        "url": full_src,
                        "timestamp": timestamp
                    })
                    
            elif content_type == "Tables":
                tables = soup.find_all('table')
                for i, table in enumerate(tables[:max_items]):
                    rows = []
                    for row in table.find_all('tr'):
                        cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                        if cells:
                            rows.append(cells)
                    
                    if rows:
                        results.append({
                            "type": "Table",
                            "table_index": i + 1,
                            "rows": rows,
                            "row_count": len(rows),
                            "timestamp": timestamp
                        })
                        
            elif content_type == "Custom Selector" and custom_selector:
                elements = soup.select(custom_selector)
                for i, element in enumerate(elements[:max_items]):
                    results.append({
                        "type": "Custom",
                        "selector": custom_selector,
                        "index": i + 1,
                        "content": element.get_text(strip=True),
                        "html": str(element),
                        "timestamp": timestamp
                    })
            
            # Store results
            self.scraped_data.extend(results)
            
            # Format output
            if content_type in ["Article Text"] and results:
                return results[0]["content"]
            elif content_type == "Tables" and results:
                output = ""
                for table in results:
                    output += f"\n\n=== Table {table['table_index']} ({table['row_count']} rows) ===\n"
                    for row in table['rows'][:10]:  # Show first 10 rows
                        output += " | ".join(row) + "\n"
                return output
            else:
                output = ""
                for item in results:
                    if item["type"] == "Link":
                        output += f"🔗 {item['text']} -> {item['url']}\n"
                    elif item["type"] == "Image":
                        output += f"🖼️ {item['alt']} -> {item['url']}\n"
                    elif item["type"] == "Custom":
                        output += f"📝 {item['content'][:100]}...\n"
                return output
                
        except requests.RequestException as e:
            return f"❌ Request Error: {str(e)}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def export_data(self, format_type):
        """Export scraped data in various formats"""
        if not self.scraped_data:
            return "No data to export"
        
        try:
            if format_type == "JSON":
                return json.dumps(self.scraped_data, indent=2)
            elif format_type == "CSV":
                df = pd.DataFrame(self.scraped_data)
                return df.to_csv(index=False)
            elif format_type == "Summary":
                summary = f"Total items scraped: {len(self.scraped_data)}\n"
                types = {}
                for item in self.scraped_data:
                    item_type = item.get('type', 'Unknown')
                    types[item_type] = types.get(item_type, 0) + 1
                
                for item_type, count in types.items():
                    summary += f"{item_type}: {count}\n"
                    
                return summary
        except Exception as e:
            return f"Export error: {str(e)}"

# Create scraper instance
scraper = WebScraperAgent()

# Enhanced interface
with gr.Blocks(title="🕷️ Web Scraper Pro", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # 🕷️ Web Scraper Pro Agent
    **Advanced web content extraction and analysis**
    
    Extract articles, links, images, tables, and custom elements with export capabilities.
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            url_input = gr.Textbox(
                label="🌐 URL to Scrape",
                placeholder="https://example.com or example.com",
                value="https://news.ycombinator.com"
            )
            
            with gr.Row():
                content_type = gr.Dropdown(
                    choices=["Article Text", "All Links", "Images", "Tables", "Custom Selector"],
                    label="Content Type",
                    value="Article Text"
                )
                max_items = gr.Slider(1, 100, value=20, label="Max Items", step=1)
            
            custom_selector = gr.Textbox(
                label="Custom CSS Selector",
                placeholder="e.g., .title, #content, article p",
                visible=False
            )
            
            scrape_btn = gr.Button("🕷️ Start Scraping", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            export_format = gr.Dropdown(
                choices=["JSON", "CSV", "Summary"],
                label="Export Format",
                value="Summary"
            )
            export_btn = gr.Button("📤 Export Data", size="sm")
            clear_data_btn = gr.Button("🗑️ Clear Data", size="sm")
    
    output_content = gr.Textbox(label="Scraped Content", lines=15, max_lines=20)
    export_output = gr.Textbox(label="Export Output", lines=8, visible=False)
    
    def toggle_custom_selector(content_type):
        return gr.update(visible=(content_type == "Custom Selector"))
    
    def show_export_output():
        return gr.update(visible=True)
    
    def clear_all_data():
        scraper.scraped_data.clear()
        return "Data cleared", gr.update(visible=False)
    
    content_type.change(toggle_custom_selector, inputs=[content_type], outputs=[custom_selector])
    scrape_btn.click(scraper.scrape_advanced, 
                    inputs=[url_input, content_type, custom_selector, max_items],
                    outputs=[output_content])
    export_btn.click(scraper.export_data, inputs=[export_format], outputs=[export_output])
    export_btn.click(show_export_output, outputs=[export_output])
    clear_data_btn.click(clear_all_data, outputs=[output_content, export_output])

if __name__ == "__main__":
    interface.launch(server_port=int(os.environ.get('AGENT_PORT', 7860)))
