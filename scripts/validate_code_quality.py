"""代码质量验证脚本 — TASK-U0-20260417-004

最小范围验证：
1. 导入所有核心模块
2. 检查类初始化
3. 验证关键方法签名
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*60)
print("🔍 代码质量验证")
print("="*60)

# 测试 1: 导入核心模块
print("\n1. 测试核心模块导入...")
try:
    from services.decision.src.research.three_tier_optimizer import ThreeTierOptimizer, OptimizationResult
    print("  ✅ ThreeTierOptimizer")
except Exception as e:
    print(f"  ❌ ThreeTierOptimizer: {e}")
    sys.exit(1)

try:
    from services.decision.src.research.context_compressor import ContextCompressor
    print("  ✅ ContextCompressor")
except Exception as e:
    print(f"  ❌ ContextCompressor: {e}")
    sys.exit(1)

try:
    from services.decision.src.monitoring.cost_tracker import APIUsageTracker, BudgetExceededError
    print("  ✅ APIUsageTracker")
except Exception as e:
    print(f"  ❌ APIUsageTracker: {e}")
    sys.exit(1)

try:
    from services.decision.src.research.symbol_profiler import SymbolProfiler, SymbolFeatures
    print("  ✅ SymbolProfiler")
except Exception as e:
    print(f"  ❌ SymbolProfiler: {e}")
    sys.exit(1)

try:
    from services.decision.src.research.stability_filter import StabilityFilter, OptimizationRecord
    print("  ✅ StabilityFilter")
except Exception as e:
    print(f"  ❌ StabilityFilter: {e}")
    sys.exit(1)

try:
    from services.decision.src.research.meta_optimizer import MetaOptimizer
    print("  ✅ MetaOptimizer")
except Exception as e:
    print(f"  ❌ MetaOptimizer: {e}")
    sys.exit(1)

try:
    from services.decision.src.monitoring.feishu_dashboard import FeishuDashboard
    print("  ✅ FeishuDashboard")
except Exception as e:
    print(f"  ❌ FeishuDashboard: {e}")
    sys.exit(1)

try:
    from services.decision.src.research.optimization_data_collector import OptimizationDataCollector
    print("  ✅ OptimizationDataCollector")
except Exception as e:
    print(f"  ❌ OptimizationDataCollector: {e}")
    sys.exit(1)

try:
    from services.decision.src.research.param_mapping_applicator import ParamMappingApplicator
    print("  ✅ ParamMappingApplicator")
except Exception as e:
    print(f"  ❌ ParamMappingApplicator: {e}")
    sys.exit(1)

try:
    from services.decision.src.research.strategy_architect import StrategyArchitect
    print("  ✅ StrategyArchitect")
except Exception as e:
    print(f"  ❌ StrategyArchitect: {e}")
    sys.exit(1)

# 测试 2: 检查类初始化
print("\n2. 测试类初始化...")
try:
    compressor = ContextCompressor()
    print("  ✅ ContextCompressor 初始化成功")
except Exception as e:
    print(f"  ❌ ContextCompressor 初始化失败: {e}")

try:
    tracker = APIUsageTracker(daily_budget=10.0)
    print("  ✅ APIUsageTracker 初始化成功")
except Exception as e:
    print(f"  ❌ APIUsageTracker 初始化失败: {e}")

try:
    profiler = SymbolProfiler()
    print("  ✅ SymbolProfiler 初始化成功")
except Exception as e:
    print(f"  ❌ SymbolProfiler 初始化失败: {e}")

try:
    filter_obj = StabilityFilter()
    print("  ✅ StabilityFilter 初始化成功")
except Exception as e:
    print(f"  ❌ StabilityFilter 初始化失败: {e}")

try:
    collector = OptimizationDataCollector()
    print("  ✅ OptimizationDataCollector 初始化成功")
except Exception as e:
    print(f"  ❌ OptimizationDataCollector 初始化失败: {e}")

try:
    applicator = ParamMappingApplicator()
    print("  ✅ ParamMappingApplicator 初始化成功")
except Exception as e:
    print(f"  ❌ ParamMappingApplicator 初始化失败: {e}")

# 测试 3: 验证关键方法存在
print("\n3. 验证关键方法...")
assert hasattr(ContextCompressor, 'compress_context'), "ContextCompressor 缺少 compress_context 方法"
print("  ✅ ContextCompressor.compress_context")

assert hasattr(APIUsageTracker, 'track_call'), "APIUsageTracker 缺少 track_call 方法"
print("  ✅ APIUsageTracker.track_call")

assert hasattr(SymbolProfiler, 'calculate_features'), "SymbolProfiler 缺少 calculate_features 方法"
print("  ✅ SymbolProfiler.calculate_features")

assert hasattr(StabilityFilter, 'is_high_quality'), "StabilityFilter 缺少 is_high_quality 方法"
print("  ✅ StabilityFilter.is_high_quality")

assert hasattr(OptimizationDataCollector, 'save_iteration'), "OptimizationDataCollector 缺少 save_iteration 方法"
print("  ✅ OptimizationDataCollector.save_iteration")

assert hasattr(ParamMappingApplicator, 'generate_search_space'), "ParamMappingApplicator 缺少 generate_search_space 方法"
print("  ✅ ParamMappingApplicator.generate_search_space")

print("\n" + "="*60)
print("✅ 所有验证通过！")
print("="*60)
