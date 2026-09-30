import { useState } from 'react';
import { clubInfo, crestUrl } from '../utils/clubs';

/** Club crest, falling back to the club's initials if the image fails. */
export function ClubBadge({ club, size = 32 }) {
  const [failed, setFailed] = useState(false);
  const url = crestUrl(club);
  if (!url || failed) {
    const initials = clubInfo(club).display.split(' ').map((w) => w[0]).join('').slice(0, 3);
    return (
      <div
        aria-label={club}
        style={{
          width: size, height: size, borderRadius: '50%', display: 'grid', placeItems: 'center',
          background: 'var(--mantine-color-dark-4)', color: 'var(--mantine-color-dark-0)',
          fontSize: size * 0.34, fontWeight: 700, flexShrink: 0,
        }}
      >
        {initials}
      </div>
    );
  }
  return (
    <img src={url} alt={`${clubInfo(club).display} crest`} width={size} height={size}
      style={{ objectFit: 'contain', flexShrink: 0 }} loading="lazy" onError={() => setFailed(true)} />
  );
}
