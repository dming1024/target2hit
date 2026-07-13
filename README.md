# Target2Hit Discovery Platform

AI-driven Target-to-Hit Discovery Pipeline — 从基因靶点出发，自动完成结构解析、口袋检测、AI 虚拟筛选、分子对接和共识排序，输出候选化合物列表及报告。

## 系统架构

```
用户输入 (Gene Symbol)
    │
    ▼
Target Assessment  ── 靶点可药性评估 (UniProt/ChemBL/OpenTargets/TCGA/DEPMAP)
    │
    ▼
Structure          ── 蛋白质结构解析 (PDB / AlphaFold)
    │
    ▼
Pocket Detection   ── 结合口袋检测 (fPocket)
    │
    ▼
AI Screening       ── 大规模虚拟筛选 (ESM2 + ChemBERTa 零样本/MLP)
    │
    ▼
Docking            ── 分子对接 (AutoDock Vina, 并行执行)
    │
    ▼
Consensus Ranking  ── 共识排序 (AI评分 + 对接能 + 类药性 + 新颖性)
    │
    ▼
Annotation & Report ── 化合物注释 (PubChem/ChEMBL) + 报告生成 (Jinja2)
```

## 目录结构

```
Target2Drug/
├── api/                    # FastAPI 应用
│   ├── main.py             #   应用入口
│   ├── schemas.py          #   Pydantic 请求/响应模型
│   └── routes/             #   API 路由
│       ├── pipeline.py     #     完整流程
│       ├── screening.py    #     虚拟筛选
│       ├── docking.py      #     分子对接
│       └── jobs.py         #     任务管理
├── workflow/               # 工作流引擎
│   ├── engine.py           #   顺序编排引擎
│   ├── contracts.py        #   模块间数据契约 (frozen dataclasses)
│   └── config.py           #   YAML 配置加载
├── target_assessment/      # 靶点可药性评估
│   ├── assessment_core.py  #   核心评估逻辑
│   ├── modules/            #   数据源模块 (ChemBL, OpenTargets, TCGA, DEPMAP)
│   └── data/               #   离线数据库
├── structure/              # 蛋白质结构解析
│   ├── resolver.py         #   UniProt → PDB/AlphaFold 查询
│   └── preparation.py      #   结构清洗 (去水/加氢/补残基)
├── pocket/                 # 口袋检测
│   └── fpocket.py          #   fPocket 封装
├── screening/              # AI 虚拟筛选
│   ├── protein_encoder.py  #   ESM2 蛋白编码器
│   ├── ligand_encoder.py   #   ChemBERTa 配体编码器
│   ├── compound_library.py #   化合物库管理
│   ├── zero_shot.py        #   零样本余弦相似度打分
│   └── mlp_head.py         #   MLP 微调头 (stub)
├── docking/                # 分子对接
│   ├── vina.py             #   AutoDock Vina 执行器
│   ├── ligand_prep.py      #   RDKit + Meeko 配体制备
│   └── parallel.py         #   并行对接调度
├── ranking/                # 共识排序
│   ├── scorer.py           #   加权评分器
│   └── filters.py          #   QED / PAINS / SA 过滤器
├── annotation/             # 化合物注释
│   └── fetcher.py          #   PubChem / ChEMBL 数据抓取
├── report/                 # 报告生成
│   ├── generator.py        #   Jinja2 报告渲染
│   └── templates/          #   HTML 报告模板
├── database/               # 数据持久化
│   ├── models.py           #   SQLAlchemy ORM 模型
│   └── session.py          #   数据库会话管理
├── scripts/
│   └── run_pipeline.py     # CLI 入口
├── configs/
│   └── default.yaml        # 默认配置
├── tests/                  # 测试 (32 passed, 3 skipped)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 环境要求

> **注意**: 本开发服务器不包含 GPU，无法运行 AI Screening (需要 PyTorch + Transformers)。模块在检测到缺少依赖时会给出明确错误提示。部署到生产环境 (带 GPU) 后安装 `torch` 和 `transformers` 即可。

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.8+ (推荐 3.10) | .python-version 指定 3.8 |
| **GPU (生产环境)** | NVIDIA + CUDA 12.1+ | AI Screening 模块需要 GPU 推理 |
| PostgreSQL | 15 | 任务和结果持久化 |
| Redis | 7 | 任务队列缓存 |
| MinIO | latest | 对象存储 (报告/结构文件) |
| fPocket | 任意 | 口袋检测二进制工具 |
| AutoDock Vina | 1.2.5 | 分子对接引擎 |

### Python 依赖

核心包见 `requirements.txt`，主要包括：
- **Web**: FastAPI 0.115, Uvicorn 0.30, Pydantic 2.9
- **ML (生产环境)**: PyTorch >= 2.0, Transformers >= 4.40 (ESM2, ChemBERTa)
- **Cheminformatics**: RDKit >= 2023.03, Meeko >= 0.5, OpenBabel
- **Bioinformatics**: Biopython >= 1.83
- **Data**: NumPy, Pandas, PyYAML
- **Database**: SQLAlchemy >= 2.0, psycopg2-binary
- **Storage**: MinIO, Redis
- **Report**: Jinja2, Plotly, WeasyPrint
- **Testing**: pytest >= 8.0, pytest-asyncio

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/dming1024/target2hit.git
cd target2hit
```

### 2. 安装依赖

**本地开发环境：**

```bash
# 创建虚拟环境
python3.8 -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 安装系统工具 (Linux)
# fPocket
sudo apt-get install fpocket

# AutoDock Vina
wget https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64 \
    -O /usr/local/bin/vina
chmod +x /usr/local/bin/vina
```

**Windows 部署：**

```powershell
# 1. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 2. 安装依赖 (跳过 openbabel-wheel，使用纯 Python 替代)
pip install -r requirements.txt

# 3. 安装 PyTorch (根据 CUDA 版本选择)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
# 或 CPU 版: pip install torch torchvision torchaudio

# 4. AutoDock Vina
#    下载 vina_1.2.7_win.exe → 重命名为 vina.exe → 放到 PATH 或项目目录

# 5. OpenBabel (可选 — 受体 PDB→PDBQT 已有纯 Python 回退)
#    conda install -c conda-forge openbabel
```

> **OpenBabel 说明**: `openbabel-wheel` (pip) 在 Windows 上需要 CMake 编译器，容易安装失败。
> 代码已内置纯 Python PDB→PDBQT 转换器作为回退，不安装 OpenBabel 也可正常运行。
> 如需更高精度，通过 conda 安装: `conda install -c conda-forge openbabel`

**Linux 部署：**

```bash
# 创建虚拟环境
python3.8 -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# fPocket
sudo apt-get install fpocket

# AutoDock Vina
wget https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64 \
    -O /usr/local/bin/vina
chmod +x /usr/local/bin/vina

# OpenBabel (可选，已经内置纯 Python 回退)
sudo apt-get install openbabel
```

**Docker 部署 (推荐，一步到位)：**

```bash
docker-compose up -d
```

这会启动四个服务：
- `api` — FastAPI 应用 (端口 8000)
- `db` — PostgreSQL 15 (端口 5432)
- `minio` — MinIO 对象存储 (API: 9000, Console: 9001)
- `redis` — Redis 7 (端口 6379)

### 3. 构建离线数据库 (可选，用于 Target Assessment)

```bash
cd target_assessment/data
python build_offline_db.py
```

这会生成 `processed/` 目录下的 CSV 和 SQLite 数据文件，用于离线靶点评估。

### 4. 运行测试

```bash
# 运行全部测试
pytest tests/ -v

# 预期结果: 32 passed, 3 skipped, 0 failed
# (跳过的 3 个测试需要下载 ESM2/ChemBERTa 模型权重)
```

### 5. CLI 运行流程

```bash
# 基础用法：对 EGFR 靶点运行完整流程
python scripts/run_pipeline.py --gene EGFR

# 指定疾病背景
python scripts/run_pipeline.py --gene EGFR --disease NSCLC

# 自定义配置和输出目录
python scripts/run_pipeline.py \
    --gene BRAF \
    --disease Melanoma \
    --config my_config.yaml \
    --output ./results/
```

示例输出：
```
Job a1b2c3d4: EGFR → Hits pipeline starting...
...
Top 5 Hits for EGFR:
  1. CHEMBL12345: 0.8723 (AI: 0.891, Dock: -9.2)
  2. CHEMBL67890: 0.8612 (AI: 0.873, Dock: -8.8)
  3. DRUGBANK001: 0.8498 (AI: 0.856, Dock: -8.5)
  4. PDBBIND_XYZ: 0.8321 (AI: 0.841, Dock: -8.1)
  5. CHEMBL11111: 0.8215 (AI: 0.829, Dock: -7.9)

Report: /tmp/target2drug/report_a1b2c3d4.json
```

### 6. 启动 API 服务

**Docker 方式 (已启动则跳过)：**

```bash
docker-compose up -d
```

**本地开发方式：**

```bash
# 确保 PostgreSQL、Redis、MinIO 可用（可用 docker-compose 单独启动它们）
docker-compose up -d db minio redis

# 启动 API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. API 使用

健康检查：
```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "0.1.0"}
```

运行完整流程：
```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "gene_symbol": "EGFR",
    "disease": "NSCLC",
    "config_overrides": {
      "pipeline": {"top_n_final": 20}
    }
  }'
```

响应：
```json
{
  "job_id": "a1b2c3d4",
  "status": "completed",
  "gene_symbol": "EGFR",
  "num_hits": 50,
  "top_hit": {
    "id": "CHEMBL12345",
    "score": 0.8723
  },
  "report_path": "/tmp/target2drug/report_a1b2c3d4.json"
}
```

其他 API 端点：
- `POST /api/v1/screening/run` — 单独运行虚拟筛选
- `POST /api/v1/docking/run` — 单独运行分子对接
- `GET /api/v1/job/{job_id}` — 查询任务状态
- `GET /api/v1/job/{job_id}/results` — 获取任务结果

完整 API 文档 (Swagger UI): `http://localhost:8000/docs`

## 配置说明

所有配置集中在 `configs/default.yaml`，可通过 `--config` 或 API 的 `config_overrides` 覆盖。

### 流程参数

```yaml
pipeline:
  top_n_screening: 500    # 虚拟筛选后保留的化合物数
  top_n_docking: 100       # 进入对接的化合物数
  top_n_final: 50          # 最终输出的命中数
```

### 筛选参数

```yaml
screening:
  mode: "zero_shot"               # 打分模式: zero_shot | mlp
  protein_model: "esm2_t30_150M_UR50D"  # ESM2 蛋白模型
  ligand_model: "ChemBERTa-77M-MLM"     # ChemBERTa 配体模型
  projection_dim: 256             # 投影维度
  batch_size: 256
  device: "auto"                  # auto | cpu | cuda
```

### 对接参数

```yaml
docking:
  exhaustiveness: 8       # Vina 搜索穷举度 (越高越精确但越慢)
  num_cpus: 4             # 并行对接 CPU 数
  box_padding: 4.0        # 对接框在口袋中心周围的扩展 (Å)
```

### 排序权重

```yaml
ranking:
  weights:
    ai_score: 0.30        # AI 虚拟筛选得分
    dock_score: 0.30      # 分子对接结合能
    drug_likeness: 0.15   # 类药性 (QED)
    novelty: 0.10         # 新颖性
    sa_penalty: 0.10      # 合成可及性惩罚
    pains_penalty: 0.05   # PAINS 过滤惩罚
```

### 化合物库

```yaml
compound_library:
  sources: ["chembl", "drugbank", "pdbbind"]
  max_compounds: 100000   # 筛选的最大化合物数
```

## 核心模块详解

### Workflow Engine

顺序编排引擎，模块按注册顺序依次执行。每个模块接收 `PipelineContext` (包含 job_id, gene_symbol, disease, config, previous_results) 并返回更新后的 Context。失败时保留部分结果用于调试。

### Target Assessment

评估靶点的可药性，整合多数据源：
- **UniProt**: 蛋白功能和结构信息
- **OpenTargets**: 靶点-疾病关联评分
- **ChemBL**: 已知配体和生物活性数据
- **TCGA**: 基因表达和突变概览
- **DEPMAP**: CRISPR 基因必要性评分 (CERES)

### Structure Preparation

通过 UniProt API 查询蛋白质结构，优先使用实验结构 (PDB)，回退到预测结构 (AlphaFold)。对结构进行清洗：去水分子、加氢、补全缺失残基。

### Pocket Detection

使用 fPocket 检测蛋白质表面的结合口袋，返回前 N 个口袋及 druggability score，按体积和可药性排序。

### AI Screening

大规模虚拟筛选的两阶段流程：
1. **编码**: ESM2 编码靶蛋白 → 蛋白嵌入向量; ChemBERTa 编码化合物 → 化合物嵌入向量
2. **打分**: 零样本余弦相似度 / MLP 预测头，选出 top-N 化合物

### Docking

对 AI 筛选后的化合物进行精确分子对接：
- RDKit + Meeko 配体制备 (3D 构象 + 电荷)
- AutoDock Vina 对接引擎
- 并行执行器 (按 CPU 数并行)

### Consensus Ranking

多维度共识排序：
- AI 虚拟筛选得分
- 分子对接结合能
- 类药性 (QED)
- 合成可及性 (SA Score)
- PAINS 过滤 (假阳性化合物)
- 新颖性评分

### Annotation & Report

- 从 PubChem / ChEMBL 获取化合物注释
- Jinja2 渲染 HTML/PDF 报告 (含 3D 分子结构图、排序表)

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `jobs` | 流程任务记录 (gene, status, config, error) |
| `compounds` | 化合物库 (SMILES, InChIKey, MW, LogP) |
| `screening_results` | AI 虚拟筛选结果 (compound, ai_score, rank) |
| `docking_results` | 分子对接结果 (compound, binding_energy, pose) |
| `ranking_results` | 共识排序结果 (final_score, 各维度得分) |

## 测试

```bash
pytest tests/ -v          # 全部测试
pytest tests/test_contracts.py -v   # 数据契约测试
pytest tests/test_engine.py -v      # 工作流引擎测试
pytest tests/test_api.py -v         # API 测试
pytest tests/test_pipeline_e2e.py -v # 端到端测试
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 启动基础设施服务
docker-compose up -d db minio redis
```

系统会在首次运行时自动下载 ESM2 和 ChemBERTa 模型权重（约 500MB），缓存于本地 `models/` 目录。

---

## 生产部署指南

以下是从开发环境迁移到生产环境的完整步骤，涵盖模型下载、AI 双塔训练、fPocket 配置、化合物库构建和生产环境清单。

### 第一步：GPU 服务器环境

**硬件要求：**

| 组件 | 最低 | 推荐 |
|------|------|------|
| GPU | NVIDIA 8GB VRAM (T4/V100) | NVIDIA 24GB+ VRAM (A100/A6000) |
| CPU | 8 cores | 16+ cores |
| RAM | 32 GB | 64+ GB |
| Disk | 50 GB (模型+数据) | 200+ GB (含化合物库) |
| OS | Ubuntu 20.04/22.04 | Ubuntu 22.04 LTS |

**基础软件安装：**

```bash
# 系统工具
sudo apt-get update
sudo apt-get install -y wget build-essential fpocket openbabel

# CUDA Toolkit (以 CUDA 12.1 为例)
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run

# Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b

# AutoDock Vina
wget https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64 \
    -O /usr/local/bin/vina && chmod +x /usr/local/bin/vina

# 创建项目环境
conda create -n target2drug python=3.10 -y
conda activate target2drug
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 第二步：下载 AI 模型

```bash
mkdir -p models

# ESM2 蛋白编码器 (~600MB, 最多 3GB 可选)
python -c "
from huggingface_hub import snapshot_download
snapshot_download('facebook/esm2_t30_150M_UR50D', local_dir='models/esm2_t30_150M_UR50D')
print('ESM2 (150M) done')
"

# 更大的 ESM2 变体（精度更高，按需选择）
# snapshot_download('facebook/esm2_t33_650M_UR50D', local_dir='models/esm2_t33_650M_UR50D')
# snapshot_download('facebook/esm2_t36_3B_UR50D', local_dir='models/esm2_t36_3B_UR50D')

# ChemBERTa 配体编码器 (~50MB)
python -c "
from huggingface_hub import snapshot_download
snapshot_download('DeepChem/ChemBERTa-77M-MLM', local_dir='models/ChemBERTa-77M-MLM')
print('ChemBERTa done')
"
```

> 国内网络慢可在脚本开头加 `import os; os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'`

**验证模型：**

```bash
python -c "
from screening.protein_encoder import ProteinEncoder
from screening.ligand_encoder import LigandEncoder
p = ProteinEncoder('esm2_t30_150M_UR50D', device='cpu')
print('Protein emb shape:', p.encode('MPSKTSLAR').shape)
l = LigandEncoder('ChemBERTa-77M-MLM', device='cpu')
print('Ligand emb shape:', l.encode('CC(=O)OC1=CC=CC=C1C(=O)O').shape)
"
# 预期输出: Protein emb shape: (640,) / Ligand emb shape: (600,)
```

### 第三步：训练 AI 双塔模型 (V2)

V1 使用零样本随机投影，AI 分数接近 0。V2 需要在已知蛋白-配体亲和力数据上训练投影矩阵或 MLP 预测头，让 AI 打分具有真实意义。训练之前需要先准备化合物库（见第四步）。

#### 3a. 零样本 → 有监督投影（轻量，推荐先行）

当前 `zero_shot.py` 使用随机投影将 ESM2 (640d) 和 ChemBERTa (600d) 映射到共享 256d 空间算余弦相似度。替换为有监督投影只需要训练一个 640×256 / 600×256 的线性层：

```python
# train/train_projection.py  — 在 BindingDB/PDBBind 上训练投影矩阵
import torch
import torch.nn as nn
import numpy as np

class ProjectionHead(nn.Module):
    def __init__(self, in_dim, out_dim=256):
        super().__init__()
        self.linear = nn.Linear(in_dim, out_dim, bias=False)

    def forward(self, x):
        return nn.functional.normalize(self.linear(x), dim=-1)

# 训练循环 (概念代码，实际需要 BindingDB 数据)
# 1. 加载已知亲和力的蛋白-配体对
# 2. 用冻结的 ESM2 / ChemBERTa 分别编码
# 3. 训练投影矩阵使余弦相似度与 pKd/pKi 值相关
#    Loss = MSE(cosine_sim(proj(prot), proj(lig)), normalized_affinity)
# 4. 保存权重到 models/projection_prot.pt, models/projection_lig.pt
#
# 训练脚本 scaffold: 见 train/train_zero_shot_projection.py
# 预期数据量: 1000+ 蛋白-配体对有已知亲和力即可开始
```

训练数据来源：
- **BindingDB** (推荐): `https://www.bindingdb.org/bind/index.jsp` — 下载 TSV，过滤 `Kd`/`Ki`/`IC50` 列
- **PDBBind** (高精度): `http://www.pdbbind.org.cn/` — X 射线结构 + 实验亲和力，约 19K 条
- **ChEMBL**: `https://www.ebi.ac.uk/chembl/` — 最大，但数据需清洗

训练完成后修改配置：

```yaml
# configs/production.yaml
screening:
  mode: "zero_shot"            # 仍用 zero_shot（但投影矩阵已训练好）
  mlp_weights: null
  projection_dim: 256
  projection_weights:          # 新增：指向训练好的投影权重
    protein: "models/projection_prot.pt"
    ligand: "models/projection_lig.pt"
```

#### 3b. MLP 预测头（更重，需要大规模数据）

当前 `mlp_head.py` 是 stub。完整的 MLP 预测头需要连接蛋白和配体嵌入，通过多层网络预测亲和力：

```python
# train/train_mlp_head.py
class MLPAffinityPredictor(nn.Module):
    def __init__(self, prot_dim=640, lig_dim=600, hidden=512):
        super().__init__()
        self.fc1 = nn.Linear(prot_dim + lig_dim, hidden)
        self.fc2 = nn.Linear(hidden, hidden // 2)
        self.fc3 = nn.Linear(hidden // 2, 1)
        self.dropout = nn.Dropout(0.3)

    def forward(self, prot_emb, lig_emb):
        x = torch.cat([prot_emb, lig_emb], dim=-1)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        return self.fc3(x).squeeze(-1)

# 训练数据: PDBBind refined set (~5K 条) 或 BindingDB 中高置信度数据 (~10K 条)
# 训练目标: 预测 pKd/pKi (RMSE < 1.0 视为可用)
# 保存: models/mlp_affinity.pt
```

训练完成后：

```yaml
screening:
  mode: "mlp"
  mlp_weights: "models/mlp_affinity.pt"
```

#### 3c. 负样本构造

训练数据大多只有正例（有亲和力的配对）。需要构造负例：
- **随机配对**: 随机蛋白 + 随机配体 → 标签为低亲和力
- **困难负例**: 结构相似但亲和力低的化合物 (Tanimoto > 0.5 但 pKd < 阈值)
- **比例**: 正负样本比 1:3 ~ 1:5

### 第四步：构建化合物库

默认使用 `CompoundLibrary.load_sample()` 加载 10 个内置样本。生产环境需要加载真实化合物库。

#### 4a. ChEMBL 化合物库 (推荐，~2M 化合物)

```bash
# 下载 ChEMBL 最新版 SQLite
wget https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_34_sqlite.tar.gz
tar -xzf chembl_34_sqlite.tar.gz

# 导出化合物为 TSV
python -c "
import sqlite3, csv
conn = sqlite3.connect('chembl_34/chembl_34_sqlite/chembl_34.db')
rows = conn.execute('''
    SELECT DISTINCT m.chembl_id, cs.canonical_smiles
    FROM compound_structures cs
    JOIN molecule_dictionary m ON cs.molregno = m.molregno
    WHERE m.molecule_type = 'Small molecule'
      AND cs.canonical_smiles IS NOT NULL
      AND m.max_phase >= 0
''').fetchall()
with open('data/chembl_compounds.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['compound_id', 'smiles'])
    w.writerows(rows)
print(f'Exported {len(rows)} compounds')
"
```

#### 4b. DrugBank (已批准/临床试验药物，~15K)

从 `https://go.drugbank.com/releases/latest` 下载（需注册），解压后用 XML 解析提取 SMILES。

#### 4c. PDBbind (有结构信息的配体，~20K)

从 `http://www.pdbbind.org.cn/` 下载 general set，提取配体 SMILES。

#### 4d. 加载到管线

```python
# 在代码中或通过 API 配置指定化合物库路径
from screening.compound_library import CompoundLibrary

library = CompoundLibrary(max_compounds=200000)
library.load_from_smiles_file("data/chembl_compounds.tsv", id_col=0, smiles_col=1)
# 或合并多个库
library.load_from_smiles_file("data/drugbank_compounds.tsv", id_col=0, smiles_col=1)
```

或者修改 `screening/__init__.py` 的 `run()` 函数，将 `library.load_sample()` 替换为实际文件加载。

#### 4e. 化合物库预处理（可选，加速筛选）

对大型库 (>100K) 可以做预过滤：

```python
# preprocess/filter_library.py
from rdkit import Chem
from rdkit.Chem import Descriptors, QED
import csv

def filter_compounds(input_tsv, output_tsv):
    """过滤掉明显不可药用的化合物"""
    kept = 0
    with open(input_tsv) as fin, open(output_tsv, 'w', newline='') as fout:
        reader = csv.reader(fin, delimiter='\t')
        writer = csv.writer(fout, delimiter='\t')
        header = next(reader)
        writer.writerow(header)
        for row in reader:
            mol = Chem.MolFromSmiles(row[1])
            if mol is None:
                continue
            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            # Lipinski-like 宽松预过滤
            if 150 < mw < 700 and -3 < logp < 7:
                writer.writerow(row)
                kept += 1
    print(f'Kept {kept} compounds')

filter_compounds('data/chembl_compounds.tsv', 'data/chembl_filtered.tsv')
```

### 第五步：配置 fPocket

fPocket 是口袋检测的核心工具，直接影响对接精度。

#### 5a. 安装

```bash
# Ubuntu/Debian
sudo apt-get install fpocket

# CentOS/RHEL (从源码编译)
git clone https://github.com/Discngine/fpocket.git
cd fpocket && make && sudo make install

# macOS
brew install brewsci/bio/fpocket

# 验证
fpocket --help
# 输出: fPocket X.X.X ...
```

#### 5b. 配置

```yaml
# configs/default.yaml
pocket:
  algorithm: "fpocket"
  top_pockets: 3             # 对前 3 个最优口袋分别对接

docking:
  box_padding: 4.0          # 口袋检测后，对接框在口袋中心周围外扩 (Å)
```

#### 5c. fPocket 工作原理

```
输入: 清洗过的 PDB 蛋白结构
  ↓
fPocket 算法:
  1. 在蛋白表面扫描，生成 alpha sphere 网格
  2. 密集的 alpha spheres → 可能的结合口袋
  3. 过滤掉太小或太浅的候选
  4. 对每个口袋计算 druggability score (0-1)
  ↓
输出: 口袋列表 (中心坐标, 尺寸, druggability_score, volume)
  ↓
Docking: 口袋中心 (± box_padding) 作为 Vina 对接盒
```

#### 5d. 无 fPocket 的回退行为

```
fPocket 不可用
  ↓
pocket/__init__.py 创建默认口袋:
  center = (0, 0, 0)   ← 非真实口袋位置!
  size   = (25, 25, 25) Å
  ↓
对接结果不准确 → 生产环境必须安装 fPocket
```

### 第六步：生产配置

合并所有生产配置：

```yaml
# configs/production.yaml
pipeline:
  top_n_screening: 500
  top_n_docking: 100
  top_n_final: 50

screening:
  mode: "zero_shot"
  protein_model: "esm2_t33_650M_UR50D"  # 升级到更大的 ESM2
  ligand_model: "ChemBERTa-77M-MLM"
  projection_dim: 256
  batch_size: 512                          # 加大 batch
  device: "cuda"

docking:
  exhaustiveness: 16                       # 生产环境提高精度
  num_cpus: 16                             # 更多并行
  box_padding: 4.0

ranking:
  weights:
    ai_score: 0.30
    dock_score: 0.35                       # 对接权重高于 AI (更可信)
    drug_likeness: 0.15
    novelty: 0.10
    sa_penalty: 0.10
    pains_penalty: 0.00                    # PAINS 已在数据库层面过滤

structure:
  prefer_experimental: true
  max_resolution: 2.5                      # 更严格的分辨率要求

pocket:
  algorithm: "fpocket"
  top_pockets: 3

compound_library:
  sources: ["chembl", "drugbank", "pdbbind"]
  max_compounds: 500000                    # 生产可扩大

database:
  url: "postgresql://target2drug:CHANGE_ME@localhost:5432/target2drug"

storage:
  endpoint: "localhost:9000"
  access_key: "CHANGE_ME"
  secret_key: "CHANGE_ME"
  bucket: "target2drug"
```

```bash
# 使用生产配置运行
python scripts/run_pipeline.py --gene EGFR --config configs/production.yaml --output ./results/
```

### 第七步：验证清单

部署完成后逐项验证：

```
□ fPocket 可用:  fpocket --help
□ Vina 可用:     vina --version
□ GPU 可用:      python -c "import torch; print(torch.cuda.is_available())"  # 应输出 True
□ ESM2 可加载:   python -c "from screening.protein_encoder import ProteinEncoder; ProteinEncoder().encode('MPSK')"
□ ChemBERTa 可加载: python -c "from screening.ligand_encoder import LigandEncoder; LigandEncoder().encode('CCO')"
□ 化合物库路径正确: ls data/chembl_compounds.tsv
□ 数据库连接:    docker-compose up -d db minio redis && curl http://localhost:8000/health
□ 全流程测试:    python scripts/run_pipeline.py --gene EGFR --config configs/production.yaml
□ 对接分数不为 0: 查看输出，dock_score 应 < -5 kcal/mol
□ AI 分数 > 0.7:  查看输出，ai_score 应 > 0.7（训练投影后）
```

### 常见问题

**Q: 对接分数全是 -1.0 或接近 0？**
A: fPocket 没安装或没正确检测口袋。检查 `fpocket --help`，确认 PDB 文件路径正确。没装 fPocket 时对接盒默认定在 (0,0,0)。

**Q: AI 分数接近 0？**
A: 零样本模式用随机投影，分数无实际意义。训练投影矩阵（第三步）后分数应有区分度。

**Q: 模型加载时还要从 HuggingFace 下载？**
A: 编码器会自动检测 `models/` 目录。确认模型文件夹结构正确（里面有 `pytorch_model.bin` 和 `config.json`）。

**Q: 内存不足 (OOM)？**
A: 减少 `compound_library.max_compounds`、`screening.batch_size`，或使用 CPU offload `device: "cpu"`。
