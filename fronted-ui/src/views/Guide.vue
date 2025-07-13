<template>
  <div class="page-container">
    <!-- 固定顶部 -->
    <div class="page-header">
      <h1 class="page-title">使用指南与常见问题</h1>
      <PageTabs
        v-model:activeTab="activeTab"
        :tabs="tabs"
        tabStyle="default"
      />
    </div>

    <!-- 可滚动内容区域 -->
    <div class="page-content">
      <div class="content-wrapper">
        <!-- 主要内容区域 -->
        <div class="guide-content">
          <!-- 加载状态 -->
          <div v-if="isLoading" class="loading-container">
            <div class="loading-spinner"></div>
            <p>正在加载内容...</p>
          </div>
          
          <!-- 使用指南内容 -->
          <div v-else-if="activeTab === 'guide'" class="markdown-content" v-html="parsedGuideContent">
          </div>
          
          <!-- 常见问题内容 -->
          <div v-else-if="activeTab === 'faq'" class="markdown-content" v-html="parsedFaqContent">
          </div>
          
          <!-- 错误信息 -->
          <div v-else-if="error" class="error-message">
            <p>{{ error }}</p>
            <button @click="fetchContent" class="retry-button">重试</button>
          </div>
        </div>
        
        <!-- 右侧目录 -->
        <div v-if="!isLoading && !error" class="toc-container">
          <div class="toc-header">目录</div>
          <div class="toc-content-wrapper">
            <div class="toc-content">
              <ul>
                <li 
                  v-for="(item, index) in currentToc" 
                  :key="index" 
                  :class="{ 'toc-h1': item.level === 1, 'toc-h2': item.level === 2, 'toc-h3': item.level === 3 }"
                >
                  <a href="javascript:void(0)" @click="scrollToHeading(item.id)">{{ item.text }}</a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { marked } from 'marked';
import PageTabs from '@/components/common/PageTabs.vue';

// 标签页定义
const tabs = [
  { key: 'guide', label: '使用指南' },
  { key: 'faq', label: '常见问题' }
];

// 状态变量
const activeTab = ref('guide');
const guideContent = ref('');
const faqContent = ref('');
const isLoading = ref(true);
const error = ref(null);
const guideToc = ref([]);
const faqToc = ref([]);

// 当前显示的目录
const currentToc = computed(() => {
  return activeTab.value === 'guide' ? guideToc.value : faqToc.value;
});

// 解析Markdown为HTML
const parsedGuideContent = computed(() => {
  return marked(guideContent.value);
});

const parsedFaqContent = computed(() => {
  return marked(faqContent.value);
});

// 处理Markdown内容，为标题添加ID
const processMarkdown = (content) => {
  const lines = content.split('\n');
  const processedLines = lines.map(line => {
    // 处理标题，添加ID
    const h1Match = line.match(/^# (.+)/);
    const h2Match = line.match(/^## (.+)/);
    const h3Match = line.match(/^### (.+)/);
    
    if (h1Match || h2Match || h3Match) {
      const match = h1Match || h2Match || h3Match;
      const text = match[1].trim();
      const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w\u4e00-\u9fa5-]/g, '');
      
      // 计算标题级别
      let level = 1;
      if (h2Match) level = 2;
      if (h3Match) level = 3;
      
      // 替换标题行，添加ID属性
      return `${'#'.repeat(level)} <a id="${id}"></a>${text}`;
    }
    
    return line;
  });
  
  return processedLines.join('\n');
};

// 从Markdown内容中提取标题生成目录
const extractToc = (content) => {
  const toc = [];
  const lines = content.split('\n');
  
  lines.forEach(line => {
    // 匹配Markdown标题格式
    const h1Match = line.match(/^# (.+)/);
    const h2Match = line.match(/^## (.+)/);
    const h3Match = line.match(/^### (.+)/);
    
    if (h1Match) {
      const text = h1Match[1].trim();
      const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w\u4e00-\u9fa5-]/g, '');
      toc.push({ level: 1, text, id });
    } else if (h2Match) {
      const text = h2Match[1].trim();
      const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w\u4e00-\u9fa5-]/g, '');
      toc.push({ level: 2, text, id });
    } else if (h3Match) {
      const text = h3Match[1].trim();
      const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w\u4e00-\u9fa5-]/g, '');
      toc.push({ level: 3, text, id });
    }
  });
  
  return toc;
};

// 滚动到指定标题
const scrollToHeading = (id) => {
  // 添加延迟确保DOM已更新
  setTimeout(() => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    } else {
      // 尝试使用querySelector查找带有id的锚点
      const anchor = document.querySelector(`a[id="${id}"]`);
      if (anchor) {
        anchor.scrollIntoView({ behavior: 'smooth' });
      } else {
        console.error(`找不到ID为${id}的元素`);
      }
    }
  }, 50);
};

// 获取文档内容
const fetchContent = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    // 使用fetch API获取Markdown文件
    const guideResponse = await fetch('/docs/guide.md');
    const faqResponse = await fetch('/docs/faq.md');
    
    if (!guideResponse.ok) {
      throw new Error(`无法加载使用指南: ${guideResponse.status}`);
    }
    
    if (!faqResponse.ok) {
      throw new Error(`无法加载常见问题: ${faqResponse.status}`);
    }
    
    const rawGuideContent = await guideResponse.text();
    const rawFaqContent = await faqResponse.text();
    
    // 提取目录
    guideToc.value = extractToc(rawGuideContent);
    faqToc.value = extractToc(rawFaqContent);
    
    // 处理Markdown内容，为标题添加ID
    guideContent.value = processMarkdown(rawGuideContent);
    faqContent.value = processMarkdown(rawFaqContent);
  } catch (err) {
    console.error('加载文档失败:', err);
    error.value = err.message || '加载文档失败，请稍后重试';
  } finally {
    isLoading.value = false;
  }
};

// 监听标签页变化
watch(activeTab, () => {
  // 切换标签页时滚动到顶部
  const contentElement = document.querySelector('.page-content');
  if (contentElement) {
    contentElement.scrollTop = 0;
  }
});

// 组件挂载时获取文档内容
onMounted(() => {
  fetchContent();
});
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: var(--background-primary);
  padding: 20px 20px 0;
  border-bottom: 1px solid var(--border-color);
  transition: var(--theme-transition);
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  transition: var(--theme-transition);
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.content-wrapper {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.guide-content {
  background-color: var(--background-secondary);
  border-radius: 12px;
  padding: 32px;
  box-shadow: var(--shadow-md);
  overflow-y: visible;
  height: auto;
  flex: 1;
  transition: var(--theme-transition);
}

/* 目录样式 */
.toc-container {
  background-color: var(--background-secondary);
  border-radius: 12px;
  box-shadow: var(--shadow-md);
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 250px);
  width: 280px;
  flex-shrink: 0;
  transition: var(--theme-transition);
}

.toc-header {
  font-size: 18px;
  font-weight: 600;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color-light);
  flex-shrink: 0;
  background-color: var(--background-secondary);
  border-radius: 12px 12px 0 0;
  position: sticky;
  top: 0;
  z-index: 1;
  color: var(--text-primary);
  transition: var(--theme-transition);
}

.toc-content-wrapper {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.toc-content-wrapper::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}

.toc-content {
  padding: 12px 0;
}

.toc-content ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc-content li {
  padding: 6px 20px;
  line-height: 1.4;
}

.toc-content a {
  color: var(--text-secondary);
  text-decoration: none;
  display: block;
  transition: var(--theme-transition);
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toc-content a:hover {
  color: var(--primary-color);
}

.toc-h1 {
  font-weight: 600;
}

.toc-h2 {
  padding-left: 36px !important;
}

.toc-h3 {
  padding-left: 52px !important;
  font-size: 13px;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color-light);
  border-top: 3px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误信息 */
.error-message {
  text-align: center;
  padding: 40px 0;
  color: var(--danger-color);
}

.retry-button {
  background-color: var(--primary-color);
  color: var(--text-primary-inverse);
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 16px;
  transition: var(--theme-transition);
}

.retry-button:hover {
  opacity: 0.9;
}

/* Markdown 内容样式 */
:deep(.markdown-content) {
  line-height: 1.7;
  color: var(--text-primary);
  width: 100%;
  overflow-x: hidden;
  word-break: break-word;
}

:deep(.markdown-content h1) {
  font-size: 28px;
  font-weight: 700;
  margin: 32px 0 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color-light);
  color: var(--text-primary);
}

:deep(.markdown-content h1:first-child) {
  margin-top: 0;
}

:deep(.markdown-content h2) {
  font-size: 24px;
  font-weight: 600;
  margin: 28px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color-light);
  color: var(--text-primary);
}

:deep(.markdown-content h3) {
  font-size: 20px;
  font-weight: 600;
  margin: 24px 0 12px;
  color: var(--text-primary);
}

:deep(.markdown-content p) {
  margin: 16px 0;
  font-size: 16px;
}

:deep(.markdown-content ul),
:deep(.markdown-content ol) {
  margin: 16px 0;
  padding-left: 24px;
}

:deep(.markdown-content li) {
  margin: 8px 0;
  font-size: 16px;
}

:deep(.markdown-content code) {
  background-color: var(--background-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.9em;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-all;
}

:deep(.markdown-content pre) {
  background-color: var(--background-tertiary);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 20px 0;
  border: 1px solid var(--border-color-light);
}

:deep(.markdown-content pre code) {
  background-color: transparent;
  padding: 0;
  display: block;
  line-height: 1.6;
  white-space: pre;
}

:deep(.markdown-content blockquote) {
  border-left: 4px solid var(--primary-color);
  padding: 12px 24px;
  background-color: color-mix(in srgb, var(--primary-color) 5%, var(--background-secondary));
  margin: 20px 0;
  color: var(--text-primary);
  border-radius: 0 8px 8px 0;
}

:deep(.markdown-content table) {
  border-collapse: collapse;
  width: 100%;
  margin: 24px 0;
  border: 1px solid var(--border-color-light);
  border-radius: 8px;
  overflow: hidden;
  display: block;
  overflow-x: auto;
}

:deep(.markdown-content th),
:deep(.markdown-content td) {
  border: 1px solid var(--border-color-light);
  padding: 12px 16px;
  text-align: left;
}

:deep(.markdown-content th) {
  background-color: var(--background-tertiary);
  font-weight: 600;
  color: var(--text-primary);
}

:deep(.markdown-content tr:nth-child(even)) {
  background-color: var(--background-tertiary);
}

:deep(.markdown-content img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 16px 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

:deep(.markdown-content a) {
  color: var(--primary-color);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: var(--theme-transition);
}

:deep(.markdown-content a:hover) {
  border-bottom-color: var(--primary-color);
}

/* 响应式布局 */
@media (max-width: 960px) {
  .content-wrapper {
    flex-direction: column;
  }
  
  .toc-container {
    display: none;
  }
}

@media (max-width: 640px) {
  .page-container {
    padding: 0;
  }
  
  .page-header {
    padding: 16px 16px 0;
  }
  
  .page-content {
    padding: 16px;
  }
  
  .guide-content {
    padding: 20px;
  }
}
</style> 