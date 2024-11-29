"use client";
import React, { useState, useEffect } from "react";
import styled from "styled-components";

const VideoUploadScreen: React.FC = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:5000/log-stream");

    eventSource.onmessage = (event) => {
      setLog((prevLogs) => [...prevLogs, event.data]);
    };

    eventSource.onerror = (error) => {
      console.error("EventSource failed: ", error);
      eventSource.close();
    };

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
      <NavBar>
        <NavItem>RedSWUS</NavItem>
      </NavBar>

      <Content>
        <HeroTitle>RedSWUS ORT</HeroTitle>
        <Subtitle>
          레드슈즈.. 설명 쓰는 곳
        </Subtitle>
        <InputBox>
          <InputLabel>Select File</InputLabel>
          <Input
            type="file"
            accept="video/*,image/png,image/jpeg"
            onChange={handleFileChange}
          />
        </InputBox>
        <UploadButton
          onClick={handleRender}
          disabled={isProcessing || !selectedFile}
        >
          {isProcessing ? "Processing..." : "Analyze"}
        </UploadButton>
      </Content>

      <LogContainer>
        <LogTitle>Processing Log</LogTitle>
        <LogContent>
          {log.map((entry, index) => (
            <LogEntry key={index}>{entry}</LogEntry>
          ))}
        </LogContent>
      </LogContainer>
    </MainContainer>
  );
};

export default VideoUploadScreen;

// Styled components
const MainContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(180deg, #eaeaea, #d9d9d9);
  color: #333;
  min-height: 100vh;
  padding: 40px 20px;
  font-family: 'Poppins', sans-serif;
  position: relative;
  overflow: hidden;
`;

const NavBar = styled.nav`
  width: 100%;
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f2f2f2;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
`;

const NavItem = styled.span`
  margin-right: 20px;
  font-size: 16px;
  color: #333;
  font-weight: bold;
  cursor: pointer;
  &:hover {
    color: #de4960;
  }
`;

const Content = styled.div`
  width: 100%;
  max-width: 1000px;
  padding: 5vw;
  background: #ffffff;
  border-radius: 15px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  text-align: center;
  margin-top: 120px;
  transition: all 0.3s ease-in-out;
  flex-grow: 1;

  @media (min-width: 1200px) {
    padding: 40px;
  }
`;

const HeroTitle = styled.h2`
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #333;
`;

const Subtitle = styled.p`
  font-size: 18px;
  margin-bottom: 40px;
  color: #555;
`;

const InputBox = styled.div`
  margin-bottom: 24px;
`;

const InputLabel = styled.label`
  font-size: 16px;
  margin-bottom: 8px;
  display: block;
  color: #333;
`;

const Input = styled.input`
  border: 1px solid #ccc;
  font-size: 16px;
  padding: 12px;
  width: 100%;
  background: #ffffff;
  color: #333;
  border-radius: 8px;
  outline: none;
  &:focus {
    border-color: #ff6347;
  }
`;

const UploadButton = styled.button`
  padding: 14px 40px;
  font-size: 17px;
  background-color: #e07b8b;
  color: #ffffff;
  border: none;
  font-weight: bold;
  border-radius: 25px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  &:hover {
    background-color: #de4960;
  }
  &:disabled {
    background-color: #e07b8b;
    cursor: not-allowed;
  }
`;

const LogContainer = styled.div`
  width: 100%;
  max-width: 1000px;
  margin-top: 40px;
  padding: 5vw;
  background: #ffffff;
  border-radius: 15px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease-in-out;
  flex-grow: 1;

  @media (min-width: 1200px) {
    padding: 40px;
  }
`;

const LogTitle = styled.h3`
  font-size: 20px;
  color: #333;
  margin-bottom: 15px;
`;

const LogContent = styled.div`
  font-size: 16px;
  color: #333;
`;

const LogEntry = styled.div`
  margin-bottom: 10px;
`;
