export default function Logo() {
  return (
    <svg
      width="80"
      height="80"
      viewBox="0 0 80 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="mb-8"
    >
      {/* Shield outline */}
      <path
        d="M40 5 L65 15 L65 35 Q65 55 40 70 Q15 55 15 35 L15 15 Z"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        className="text-teal-400"
      />

      {/* Rising graph line inside shield */}
      <path
        d="M25 50 L32 42 L38 45 L45 32 L52 35 L58 25"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        className="text-teal-300"
      />

      {/* Graph points */}
      <circle cx="25" cy="50" r="2" fill="currentColor" className="text-teal-300" />
      <circle cx="32" cy="42" r="2" fill="currentColor" className="text-teal-300" />
      <circle cx="38" cy="45" r="2" fill="currentColor" className="text-teal-300" />
      <circle cx="45" cy="32" r="2" fill="currentColor" className="text-teal-300" />
      <circle cx="52" cy="35" r="2" fill="currentColor" className="text-teal-300" />
      <circle cx="58" cy="25" r="2" fill="currentColor" className="text-teal-300" />
    </svg>
  );
}
