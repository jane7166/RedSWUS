import React from "react";

interface Props {
  log: string[];
}

const LogViewer: React.FC<Props> = ({ log }) => {
  return (
    <div>
      <h3>Process Log</h3>
      {log.map((entry, i) => (
        <div key={i}>{entry}</div>
      ))}
    </div>
  );
};

export default LogViewer;
