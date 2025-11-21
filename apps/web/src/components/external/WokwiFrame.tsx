import React from "react";

const WokwiFrame: React.FC<{ board: string }> = ({ board }) => {
  const url = `https://wokwi.com/projects/new?simulate=1&board=${board}`;
  return (
    <div className="rounded-lg overflow-hidden border bg-white">
      <iframe src={url} title="Wokwi" className="w-full h-[420px]" sandbox="allow-scripts allow-same-origin allow-modals" />
    </div>
  );
};

export default WokwiFrame;
