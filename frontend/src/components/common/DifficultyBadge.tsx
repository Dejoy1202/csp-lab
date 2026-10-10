import React from "react";
import type { Difficulty } from "../../types";
import { formatDifficulty, getDifficultyColor } from "../../utils/format";

interface DifficultyBadgeProps {
  difficulty: Difficulty;
  size?: "sm" | "md";
}

export const DifficultyBadge: React.FC<DifficultyBadgeProps> = ({
  difficulty,
  size = "md",
}) => {
  const colorClass = getDifficultyColor(difficulty);
  const text = formatDifficulty(difficulty);

  return <span className={`tag ${colorClass} size-${size}`}>{text}</span>;
};
