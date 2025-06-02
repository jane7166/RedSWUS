import React from "react";
import styled from "styled-components";

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  setLog: React.Dispatch<React.SetStateAction<string[]>>;
  selectedFile: File | null;
  isProcessing: boolean;
  onAnalyze: () => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onFileSelect, setLog, selectedFile, isProcessing, onAnalyze }) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      const file = e.target.files[0];
      onFileSelect(file);
      setLog(["File selected. Ready to render."]);
    }
  };

  return (
    <Wrapper>
      {!selectedFile ? (
        <>
          <HiddenInput
            id="file-upload"
            type="file"
            accept="video/*,image/*"
            onChange={handleChange}
          />
          <StyledLabel htmlFor="file-upload">
            <span>파일 업로드</span>
          </StyledLabel>
        </>
      ) : (
        <AnalyzeButton onClick={onAnalyze} disabled={isProcessing}>
          {isProcessing ? "분석 중..." : "분석하기"}
        </AnalyzeButton>
      )}
    </Wrapper>
  );
};

export const UploadControls: React.FC<{
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  isProcessing: boolean;
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>;
  setLog: React.Dispatch<React.SetStateAction<string[]>>;
}> = ({ onFileSelect, selectedFile, isProcessing, setIsProcessing, setLog }) => {

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
    <Wrapper>
      <ButtonRow>
        <FileUploader
          onFileSelect={onFileSelect}
          setLog={setLog}
          selectedFile={selectedFile}
          isProcessing={isProcessing}
          onAnalyze={handleRender}
        />
      </ButtonRow>
    </Wrapper>
  );
};

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
`;

const ButtonRow = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 32px;
  margin-top: 16px;
`;

const HiddenInput = styled.input`
  display: none;
`;

const StyledLabel = styled.label`
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 32px;
  background: rgba(255, 255, 255, 0.05);
  color: rgb(192, 88, 88);
  border: 2px solid rgb(192, 88, 88);
  font-weight: 500;
  border-radius: 40px;
  cursor: pointer;
  backdrop-filter: blur(12px);
  font-size: 15px;
  transition: all 0.3s ease;
  text-shadow: 0 1px 1px rgba(0,0,0,0.3);

  svg {
    transition: transform 0.3s ease;
  }

  &:hover {
    background: rgba(255, 77, 109, 0.1);
    color: #ff4d6d;
    svg {
      transform: scale(1.1);
    }
  }
`;

export const AnalyzeButton = styled.button`
  padding: 14px 36px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.05);
  color:rgb(252, 245, 246);
  border: 2px solid rgb(192, 88, 88);
  border-radius: 40px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  backdrop-filter: blur(10px);
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.3);

  &:hover {
    background: rgba(255, 77, 109, 0.1);
    color: #ff4d6d;
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: none;
  }
`;
