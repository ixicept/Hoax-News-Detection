<script lang="ts">
    export let value: number = 0.9;
    export let color: string = "#3490dc";
    const radius = 40;
    const stroke = 10;
    const norm = 2 * Math.PI * radius;
    $: offset = norm * (1 - value);
  </script>
  
  <svg width="100" height="100" class="block mx-auto">
    <circle
      cx="50"
      cy="50"
      r={radius}
      fill="none"
      stroke="#e5e7eb"
      stroke-width={stroke}
    />
    <circle
      cx="50"
      cy="50"
      r={radius}
      fill="none"
      stroke={color}
      stroke-width={stroke}
      stroke-linecap="round"
      stroke-dasharray={norm}
      stroke-dashoffset={offset}
      transform="rotate(-90 50 50)"
    />
    <text
      x="50"
      y="55"
      text-anchor="middle"
      fill={color}
      font-size="1.5em"
      font-weight="bold"
    >{Math.round(value * 100)}%</text>
  </svg>  