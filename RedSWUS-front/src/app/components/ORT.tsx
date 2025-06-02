import React, { useEffect, useState } from "react";
import styled from "styled-components";

const ORT = () => {
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScroll = window.scrollY;

      setLastScrollY(currentScroll);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [lastScrollY]);

  return (
    <HeroSection>
      <Title>ORT</Title>
      <Description>
        Unintended Text Recognition from Eyeglass Reflections
      </Description>
      <ScrollHint>↓ Using ORT</ScrollHint>
    </HeroSection>
  );
};

export default ORT;

const HeroSection = styled.section`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
  padding-top: 60px;
`;

const Title = styled.h1`
  font-size: 48px;
  color: #fff;
`;

const Description = styled.p`
  font-size: 20px;
  color: #ffccd5;
  margin-top: 10px;
`;

const ScrollHint = styled.div`
  margin-top: 40px;
  font-size: 16px;
  color: #ff6b81;
  animation: bounce 2s infinite;
  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(8px); }
  }
`;
