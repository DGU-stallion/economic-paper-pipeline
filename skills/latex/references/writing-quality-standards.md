# Writing Quality Standards — 论文写作质量标准

## 定位

本文档是 `writer-agent` 的质量检查参考，提供具体的检查清单、高频词警告、句式结构规范、论证质量标准。

> **设计边界**：这些规则提高写作质量，不是图灵测试规避工具。目标是清晰、精确、有变化的学术散文，不是骗过 AI 检测器。

---

## A. 高频词警告

以下词汇在 AI 生成文本中出现频率异常高。**不是禁用**，但每次使用时问自己："这是最精确的词吗？还是我在默认使用它？"

| 词汇 | 问题 | 推荐替代 |
|------|------|---------|
| delve | "探索"的过度替代 | examine, investigate, analyze |
| tapestry | 陈腐隐喻 | network, interplay, system |
| landscape | 非字面义时模糊 | field, domain, context |
| pivotal | 虚高重要性 | important, significant, central |
| crucial | 同上 | essential, necessary, critical |
| foster | 抽象动词 | promote, develop, cultivate |
| showcase | 非学术语域 | demonstrate, illustrate, present |
| testament | 陈腐 | evidence, indicator |
| navigate | 非本义时模糊 | manage, address, handle |
| leverage | 商业行话 | use, employ, apply |
| realm | 过时/诗意 | domain, field, area |
| embark | "开始"的过度替代 | begin, initiate, undertake |
| underscore | 过度使用 | emphasize, highlight |
| multifaceted | 模糊的复杂度 | complex, varied, diverse |
| nuanced | 空洞 | subtle, detailed, qualified |
| comprehensive | 常不实 | thorough, extensive, broad |
| robust | 模糊质量声明 | reliable, strong, rigorous |
| intricate | 同 multifaceted | complex, detailed, elaborate |
| cornerstone | 陈腐隐喻 | foundation, basis, core element |
| paradigm | 科学哲学外过度使用 | framework, model, approach |
| synergy | 商业行话 | interaction, cooperation |
| holistic | 无定义时模糊 | comprehensive, integrated |
| streamline | 非学术 | simplify, optimize |
| cutting-edge | 陈腐 | recent, advanced, novel |
| groundbreaking | 虚高 | novel, innovative, original |

### 例外规则

如果标记词是**目标学科的标准术语**，免检：
- `paradigm shift` 在科学哲学语境 → 通过
- `robust` 在统计学术语中（"robust estimator"）→ 通过
- `landscape` 在地理学/生态学字面义 → 通过

---

## B. 句式结构规范

### B.1 句子长度变化 (Burstiness)

好的学术写作有自然的句子长度变化。短句创造冲击，长句发展复杂观点。

| 章节 | 目标变化度 |
|------|-----------|
| 摘要 | 中等变化（平稳叙述） |
| 引言 | 高变化（短句钩子 → 长句展开） |
| 文献综述 | 中等（平稳分析 + 偶尔短句综合） |
| 方法 | 低变化可接受（程序性段落自然均长） |
| 结果 | 中等（关键发现短句 → 细节描述长句） |
| 结论 | 最高变化（强调用短句，解释用长句） |

**检测规则**: 连续 5 句以上落在狭窄长度范围（如都在 20-25 字），标记审查。

### B.2 主谓宾正常语序

- 先主语，再谓语，最后宾语
- ❌ "行为主体在面临暂时性收入波动时用来平滑消费的保险机制是五花八门的"
- ✅ "人们采用多种保险机制平滑消费"

### B.3 减少从句嵌套

- 句子中从句不超过一层
- 尽量减少标点分隔的非独立句子成分数量
- ❌ "基于 Roberts et al. (2012) 提出的、被广泛应用于企业层面分析的、衡量融资约束的 SA 指数，本文发现……"
- ✅ "本文采用 SA 指数 (Roberts et al., 2012) 衡量融资约束，发现……"

### B.4 "This" 必须有明确的指代对象

- ❌ "This shows that..."
- ✅ "This regression shows that..."
- ❌ "These suggest that..."
- ✅ "These results suggest that..."

### B.5 "Where" vs "in which"

- ❌ "models where consumers have uninsured shocks"
- ✅ "models in which consumers have uninsured shocks"

### B.6 疑问句和设问

- 适度使用设问句可引导读者思考
- 每篇论文不超过 2 个设问句
- ❌ "然而，这是否意味着数字经济真的促进了就业？答案是复杂的。"
- ✅ "数字经济真的促进了就业吗？本文的实证结果表明……"

---

## C. 标点控制

### C.1 破折号（—）

- 每篇论文 ≤ 3 个，建议 0-1 个
- AI 文本过度使用破折号做插入语
- 修复：替换为逗号、括号或另起一句

### C.2 分号

- ≤ 2 个/1000 词
- AI 文本倾向用分号链接独立子句，句号更清晰
- 修复：用句号另起一句

### C.3 冒号列表

- 避免连续两段都以冒号+列表开头
- 修复：将列表项融入正文，或合并为一个列表

---

## D. 清嗓子开头（直接删除）

| 短语 | 处理 |
|------|------|
| "值得注意的是……" | 删除。直接说事。 |
| "不可否认的是……" | 同上 |
| "在……的背景下" | 直接说背景，不要这个架子 |
| "基于……的分析" | "本文利用……分析" |
| "It is important to note that..." | 删除。重要的内容自会说话。 |
| "In the realm of..." | 删除。直接说主语。 |
| "It goes without saying that..." | 删除。不说也知道的就不用说。 |
| "In order to..." | 替换为 "To..." |
| "It should be noted that..." | 删除。直接 note 就行。 |
| "This serves as a testament to..." | 替换为直接说法 |
| "In today's rapidly evolving..." | 删除。过时的套话。 |
| "When it comes to..." | 替换为直接主语 |

### 元评论（Meta-commentary）

描述"论文在做什么"的句子也要避免：
- ❌ "本节将讨论……" → 直接讨论
- ❌ "以下段落考察……" → 直接考察
- ❌ "我们现在将注意力转向……" → 直接说

**例外**：引言中的路线图句子是标准实践，保留。
- ✅ "第二部分进行文献综述；第三部分介绍数据与方法。"

---

## E. 结构模式警告

### E.1 三段论强迫症 (Rule of Three Compulsion)

- ❌ 每个论点总是 3 个子点
- 两个好点胜过三个凑数的。2 个可以，5 个也可以。证据决定数量。

### E.2 段落长度均一

- ❌ 所有段落都在 150-200 字
- 自然写作有段落长度变化。短段落做强调，长段落做复杂论证。

### E.3 同义替换循环 (Synonym Cycling)

- ❌ 一段内用 3+ 同义词替换同一概念
- 学术写作中，术语一致性是美德。"学生 → 学习者 → 参与者 → 被试" 在同一段内交替出现只会让读者困惑。

### E.4 二元对比过度 (Binary Contrast Overuse)

- ❌ "不是 X。而是 Y。" 的修辞模式使用超过 2 次
- 这个修辞手法有效，但重复使用就成了怪癖。

### E.5 镜像结构

- ❌ 每个小节都是 "论点句 → 3 个证据点 → 综合句" 的模板
- 不同部分有不同的功能，应该有不同的内部节奏。

---

## F. 经济学特有质量标准

### F.1 系数报告规范

- 有效数字：小数点后 2-3 位
  - β = 4.56783 (0.67890) → β = 4.57 (0.68)
  - β = 0.2773492 (0.0934781) → β = 0.277 (0.093)
- 必须报告经济显著性
  - ✅ "数字经济发展指数每提高 1 个标准差，三产就业占比提高 0.28 个百分点"
  - ❌ "系数在 1% 水平上显著为正"

### F.2 表格规范

- T1（描述性统计）：观测数、均值、标准差、最小/最大值
- T2（基准回归）：M1 → M6 渐进控制，报告标准误而非 t 值
- 表注：\* p<0.1, \*\* p<0.05, \*\*\* p<0.01
- 表在上，注在下

### F.3 引用规范

- 中文期刊使用 GB/T 7714-2015 或期刊自定义格式
- 英文使用 Chicago Author-Date 或 APA
- 英文人名在中文期刊中保留原文：Smith (2023) 而非 史密斯 (2023)
- 3 位及以上作者：第一作者 et al.（英文）/ 第一作者等（中文）

---

## G. 自我评分指引（内部使用，不向用户报告）

每个章节完成后，按以下类别追踪违规：

| 类别 | 0 违规 | 1-3 违规 | 4+ 违规 |
|------|--------|---------|---------|
| 高频词 | 干净 | 微小 — 自行修复 | 模式问题 — 重审写法 |
| 句式结构 | 干净 | 微小 — 自行修复 | 模式问题 — 重审写法 |
| 标点 | 干净 | 微小 — 自行修复 | 模式问题 — 重审写法 |
| 清嗓子 | 干净 | 微小 — 自行修复 | 模式问题 — 重审写法 |
| 结构模式 | 干净 | 微小 — 自行修复 | 模式问题 — 重审写法 |
| 系数规范 | 干净 | 微小 — 自行修复 | 模式问题 — 重审写法 |

违规在写作过程中自行修复，不要向用户报告分数。
