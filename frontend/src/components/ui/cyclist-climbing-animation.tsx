"use client";

export function CyclistClimbingAnimation() {
  return (
    <div className="relative w-80 h-80 flex items-center justify-center">
      <svg
        viewBox="0 0 400 400"
        className="w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Mountain silhouette background */}
        <g opacity="0.1">
          <path
            d="M 50 350
               L 100 280
               Q 120 250, 150 240
               Q 180 230, 200 200
               L 220 170
               Q 240 140, 270 130
               Q 300 120, 320 90
               L 340 50
               L 350 50
               L 350 350 Z"
            fill="#8B5CF6"
          />
        </g>

        {/* Sa Calobra inspired road - dramatic hairpins */}
        <path
          d="M 80 340
             L 140 300
             Q 170 285, 200 295
             Q 230 305, 260 295
             L 300 270
             Q 280 250, 250 255
             Q 220 260, 190 250
             L 150 225
             Q 180 210, 210 220
             Q 240 230, 270 220
             L 310 190
             Q 290 170, 260 175
             Q 230 180, 200 170
             L 160 145
             Q 190 130, 220 140
             Q 250 150, 280 140
             L 320 110
             L 350 80"
          stroke="#8B5CF6"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.25"
        />

        {/* Active road progress */}
        <path
          d="M 80 340
             L 140 300
             Q 170 285, 200 295
             Q 230 305, 260 295
             L 300 270
             Q 280 250, 250 255
             Q 220 260, 190 250
             L 150 225
             Q 180 210, 210 220
             Q 240 230, 270 220
             L 310 190
             Q 290 170, 260 175
             Q 230 180, 200 170
             L 160 145
             Q 190 130, 220 140
             Q 250 150, 280 140
             L 320 110
             L 350 80"
          stroke="#8B5CF6"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.6"
          strokeDasharray="1400"
          strokeDashoffset="1400"
        >
          <animate
            attributeName="stroke-dashoffset"
            from="1400"
            to="0"
            dur="6s"
            repeatCount="indefinite"
          />
        </path>

        {/* Cyclist icon */}
        <g className="cyclist">
          {/* Cyclist circle */}
          <circle
            cx="0"
            cy="0"
            r="14"
            fill="#8B5CF6"
          >
            <animate
              attributeName="r"
              values="14;16;14"
              dur="0.8s"
              repeatCount="indefinite"
            />
          </circle>

          {/* Cyclist symbol - bike icon */}
          <g stroke="white" strokeWidth="2.5" strokeLinecap="round" fill="none">
            {/* Wheels */}
            <circle cx="-5" cy="3" r="3.5" strokeWidth="2"/>
            <circle cx="5" cy="3" r="3.5" strokeWidth="2"/>
            {/* Frame */}
            <line x1="-5" y1="3" x2="0" y2="-4" />
            <line x1="0" y1="-4" x2="5" y2="3" />
            <line x1="-2" y1="0" x2="2" y2="0" />
            {/* Rider head */}
            <circle cx="0" cy="-8" r="2.5" fill="white" />
          </g>

          {/* Animate along the Sa Calobra path */}
          <animateMotion
            dur="6s"
            repeatCount="indefinite"
            path="M 80 340
                 L 140 300
                 Q 170 285, 200 295
                 Q 230 305, 260 295
                 L 300 270
                 Q 280 250, 250 255
                 Q 220 260, 190 250
                 L 150 225
                 Q 180 210, 210 220
                 Q 240 230, 270 220
                 L 310 190
                 Q 290 170, 260 175
                 Q 230 180, 200 170
                 L 160 145
                 Q 190 130, 220 140
                 Q 250 150, 280 140
                 L 320 110
                 L 350 80"
          />
        </g>

        {/* Turn markers */}
        <g opacity="0.5" className="text-xs">
          <text x="310" y="275" fill="#8B5CF6" fontSize="11" fontWeight="500">Turn 1</text>
          <text x="135" y="230" fill="#8B5CF6" fontSize="11" fontWeight="500">Turn 2</text>
          <text x="320" y="195" fill="#8B5CF6" fontSize="11" fontWeight="500">Turn 3</text>
          <text x="145" y="150" fill="#8B5CF6" fontSize="11" fontWeight="500">Turn 4</text>
        </g>

        {/* Summit indicator */}
        <g opacity="0.7">
          <circle cx="350" cy="80" r="8" fill="none" stroke="#10B981" strokeWidth="2.5">
            <animate
              attributeName="r"
              values="8;12;8"
              dur="2s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values="0.8;0.2;0.8"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
          <circle cx="350" cy="80" r="4" fill="#10B981">
            <animate
              attributeName="opacity"
              values="0.7;1;0.7"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
        </g>
      </svg>
    </div>
  );
}
