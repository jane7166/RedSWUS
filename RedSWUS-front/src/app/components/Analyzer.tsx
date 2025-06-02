import React from "react";
import { AnalyzeButton } from "./fileUpload"; // 버튼 컴포넌트 import

interface Props {
  selectedFile: File | null;
  isProcessing: boolean;
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>;
  setLog: React.Dispatch<React.SetStateAction<string[]>>;
}

const Analyzer: React.FC<Props> = ({
  selectedFile,
  isProcessing,
  setIsProcessing,
  setLog,
}) => {
  const handleRender = async () => {
    if (!selectedFile) {
      setLog((prev) => [...prev, "No file selected."]);
      return;
    }

    setIsProcessing(true);
    setLog((prev) => [...prev, "Processing started..."]);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://localhost:5001/full_pipeline", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      setLog((prev) => [
        ...prev,
        "Processing completed.",
        `Result: ${JSON.stringify(result.str_result)}`,
      ]);
    } catch {
      setLog((prev) => [...prev, "Error processing the file."]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <AnalyzeButton onClick={handleRender} disabled={!selectedFile || isProcessing}>
      {isProcessing ? "🔄 분석 중..." : "🔍 분석하기"}
    </AnalyzeButton>
  );
};

export default Analyzer;
