"use client";
import React, { useState, useEffect } from "react";
import styled from "styled-components";

const VideoUploadScreen: React.FC = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    // SSE 연결 설정
    const eventSource = new EventSource("http://localhost:5000/log-stream");

    // 서버로부터 메시지를 받을 때마다 로그에 추가
    eventSource.onmessage = (event) => {
      console.log("Received event:", event.data);  // 로그 출력
      setLog((prevLogs) => [...prevLogs, event.data]);
    };

    // 에러 처리
    eventSource.onerror = (error) => {
      console.error("EventSource failed: ", error);
      eventSource.close(); // 에러 발생 시 연결 닫기
    };

    // 컴포넌트가 언마운트될 때 SSE 연결 해제
    return () => {
      eventSource.close();
    };
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.length) {
      setSelectedFile(event.target.files[0]);
      setLog(["File selected. Ready to render."]);
    }
  };

  const handleRender = async () => {
    if (selectedFile) {
      setIsProcessing(true);
      setLog((prevLog) => [...prevLog, "Processing started..."]);

      // Flask 서버로 파일을 전송
      const formData = new FormData();
      formData.append("file", selectedFile);

      try {
        const response = await fetch("http://localhost:5000/upload", {
          method: "POST",
          body: formData,
        });

        const result = await response.json();
        setIsProcessing(false);
        setLog((prevLog) => [
          ...prevLog,
          "Processing completed.",
          `Result: ${result.message}`,
        ]);
      } catch (error) {
        setIsProcessing(false);
        setLog((prevLog) => [...prevLog, "Error processing the file."]);
      }
    } else {
      setLog((prevLog) => [
        ...prevLog,
        "No file selected. Please select a file to process.",
      ]);
    }
  };

  return (
    <MainContainer>
      <Header>
        <BackIcon>←</BackIcon>
        <Title>Webcam Peeking Attack</Title>
      </Header>

      <ContentAndLogContainer>
        <Content>
          <SectionTitle>Upload your file</SectionTitle>
          <InfoBox>
            <p>Select a video or image file to upload.</p>
            <p>Supported formats: MP4, AVI, MOV, JPG, PNG.</p>
            <p>Max file size: 50MB.</p>
          </InfoBox>

          <InputBox>
            <InputLabel>Select File</InputLabel>
            <Input
              type="file"
              accept="video/*,image/png,image/jpeg"
              onChange={handleFileChange}
            />
          </InputBox>

          <Footer>
            <UploadButton
              onClick={handleRender}
              disabled={isProcessing || !selectedFile}
            >
              {isProcessing ? "Processing..." : "Render"}
            </UploadButton>
          </Footer>
        </Content>

        <LogContainer>
          <LogTitle>Processing Log</LogTitle>
          <LogContent>
            {log.map((entry, index) => (
              <LogEntry key={index}>{entry}</LogEntry>
            ))}
          </LogContent>
        </LogContainer>
      </ContentAndLogContainer>
    </MainContainer>
  );
};

export default VideoUploadScreen;


// Styled components
const MainContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #f8f8f8;
  color: #333;
  min-height: 100vh;
  padding-bottom: 80px;
  font-family: 'Poppins', sans-serif;
`;

const Header = styled.div`
  width: 100%;
  padding: 16px;
  background-color: #760c0c;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 22px;
  font-weight: bold;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
`;

const BackIcon = styled.span`
  font-size: 22px;
  cursor: pointer;
`;

const Title = styled.h1`
  flex-grow: 1;
  text-align: center;
  margin: 0;
  font-size: 22px;
  font-weight: 500;
`;

const ContentAndLogContainer = styled.div`
  display: flex;
  width: 100%;
  max-width: 1000px;
  margin-top: 20px;
  justify-content: space-between;
`;

const Content = styled.div`
  width: 100%;
  max-width: 600px;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  margin-bottom: 16px;
  color: #333;
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const InfoBox = styled.div`
  padding: 16px;
  background-color: #f8f8f8;
  border-radius: 6px;
  margin-bottom: 20px;
  p {
    margin: 6px 0;
    font-size: 14px;
    color: #555;
  }
`;

const InputBox = styled.div`
  margin-bottom: 24px;
`;

const InputLabel = styled.label`
  font-size: 14px;
  margin-bottom: 8px;
  display: block;
  color: #333;
`;

const Input = styled.input`
  border: 1px solid #ccc;
  font-size: 16px;
  padding: 12px;
  width: 100%;
  background-color: #fff;
  color: #333;
  border-radius: 6px;
  outline: none;
  &:focus {
    border-color: #760c0c;
  }
`;

const Footer = styled.div`
  display: flex;
  justify-content: center;
`;

const UploadButton = styled.button`
  padding: 12px 30px;
  font-size: 16px;
  background-color: #760c0c;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  &:hover {
    background-color: #5e0a0a;
  }
  &:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
`;

const LogContainer = styled.div`
  width: 280px;
  padding: 20px;
  background-color: #f4f4f4;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  overflow-y: auto;
`;

const LogTitle = styled.h3`
  margin-top: 0;
  font-size: 16px;
  color: #333;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
`;

const LogContent = styled.div`
  font-size: 14px;
  color: #555;
`;

const LogEntry = styled.div`
  margin-bottom: 10px;
  color: #760c0c;
`;
