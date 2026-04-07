from __future__ import annotations

from typing import Any

import numpy as np
import onnxruntime as rt  # type: ignore[import-untyped,import-not-found]
import onnxmltools  # type: ignore[import-untyped,import-not-found]
from onnxmltools.convert.common.data_types import FloatTensorType  # type: ignore[import-untyped,import-not-found]


class OnnxExporter:
    """XGBoost → ONNX 导出（生产推理）。

    若 onnxmltools 或 onnxruntime 未安装，模块导入时直接抛出 ImportError（不吞错）。
    导出后执行一次推理验证，确认 ONNX 模型可用。
    """

    def export(
        self,
        model: Any,
        feature_names: list[str],
        output_path: str,
    ) -> str:
        """将 XGBoost 模型导出为 ONNX 格式并写入 output_path。

        步骤：
        1. 使用 onnxmltools.convert_xgboost 转换模型
        2. 序列化写文件
        3. 加载并执行一次 dummy 推理验证导出成功

        Returns
        -------
        str
            写入的 ONNX 文件路径。
        """
        n_features = len(feature_names)
        initial_types = [("float_input", FloatTensorType([None, n_features]))]

        onnx_model = onnxmltools.convert_xgboost(
            model, initial_types=initial_types
        )

        with open(output_path, "wb") as f:
            f.write(onnx_model.SerializeToString())

        # 验证：加载并执行一次推理
        sess = rt.InferenceSession(output_path)
        dummy = np.zeros((1, n_features), dtype=np.float32)
        input_name = sess.get_inputs()[0].name
        sess.run(None, {input_name: dummy})

        return output_path
