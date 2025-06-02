"use client";
import React, { useState, useEffect } from "react";
import styled from "styled-components";
import Hero from "./components/ORT";
import { UploadControls } from "./components/fileUpload"; 
import LogViewer from "./components/Log";
import { motion } from "framer-motion";

const VideoUploadScreen: React.FC = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:5001/log-stream");

    eventSource.onmessage = (event) => {
      setLog((prevLogs) => [...prevLogs, event.data]);
    };

    eventSource.onerror = () => {
      console.error("EventSource failed.");
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <MainContainer>
      <NavBar visible={true}>
        <NavItem>RedSWUs</NavItem>
        <NavItem>Abstract</NavItem>
        <NavItem>Contact</NavItem>
        <NavItem>About</NavItem>
        <NavItem>GitHub</NavItem>
      </NavBar>
      <SnapSection>
        <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <Hero />
        </motion.div>
      </SnapSection>
      <SnapSection>
        <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        <Card>
          <SectionTitle>ORT 체험하기</SectionTitle>
          <UploadControls
            onFileSelect={setSelectedFile}
            selectedFile={selectedFile}
            isProcessing={isProcessing}
            setIsProcessing={setIsProcessing}
            setLog={setLog}
          />
        </Card>
        </motion.div>
      </SnapSection>
      <SnapSection>
        <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <LogCard>
            <SectionTitle>처리 로그</SectionTitle>
            <LogViewer log={log} />
          </LogCard>
        </motion.div>
      </SnapSection>
    </MainContainer>
  );
};

export default VideoUploadScreen;

const NavBar = styled.nav<{ visible: boolean }>`
  width: 100%;
  padding: 20px 40px;
  display: ${({ visible }) => (visible ? "flex" : "none")};
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 0, 0, 0.61);
  box-shadow: 0 5px 30px rgba(106, 29, 29, 0.68);
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
`;


const NavItem = styled.span`
  margin-right: 20px;
  font-size: 16px;
  color:rgb(141, 26, 26);
  font-weight: bold;
  cursor: pointer;
  &:hover {
    color: rgba(181, 1, 31, 0.64);
  }
`;

const MainContainer = styled.div`
  scroll-snap-type: y mandatory;
  overflow-y: scroll;
  height: 100vh;
  scroll-behavior: smooth;
  background: linear-gradient(to bottom, #0a0203, #1a0b0e);
  color: #fff;
  font-family: "Poppins", sans-serif;
`;

const SnapSection = styled.section`
  scroll-snap-align: start;
  min-height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const Card = styled.div`
  background: rgba(80, 0, 30, 0.3);
  backdrop-filter: blur(20px);
  padding: 40px;
  border-radius: 20px;
  width: 80vw;
  max-width: 1200px;
  box-shadow: 0 12px 24px rgba(255, 0, 70, 0.15);
`;

const LogCard = styled(Card)`
  max-height: 60vh;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #ff4d6d;
    border-radius: 3px;
  }
`;

const SectionTitle = styled.h2`
  font-size: 24px;
  color: rgb(192, 88, 88);
  margin-bottom: 20px;
`;
