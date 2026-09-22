import * as React from 'react';

export interface AvatarProps extends React.HTMLAttributes<HTMLSpanElement> {
  src?: string;
  name?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  isBordered?: boolean;
}

export const Avatar = React.forwardRef<HTMLSpanElement, AvatarProps>(
  ({ src, name, size = 'md', color = 'default', isBordered = false, ...props }, ref) => {
    const [hasError, setHasError] = React.useState(false);

    const getInitials = (str: string) => {
      return str
        .split(' ')
        .map((part) => part[0])
        .slice(0, 2)
        .join('')
        .toUpperCase();
    };

    return (
      <span
        ref={ref}
        data-ui="avatar"
        data-size={size}
        data-color={color}
        data-bordered={isBordered ? '' : undefined}
        {...props}
      >
        {src && !hasError ? (
          <img
            src={src}
            alt={name || 'Avatar'}
            data-ui="avatar-img"
            onError={() => setHasError(true)}
          />
        ) : (
          <span data-ui="avatar-fallback" aria-hidden="true">
            {name ? getInitials(name) : '👤'}
          </span>
        )}
      </span>
    );
  }
);

Avatar.displayName = 'Avatar';

export interface AvatarGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  max?: number;
}

export function AvatarGroup({ max, children, ...props }: AvatarGroupProps) {
  const childrenArray = React.Children.toArray(children);
  const count = max ? Math.min(max, childrenArray.length) : childrenArray.length;
  const visible = childrenArray.slice(0, count);
  const remaining = childrenArray.length - count;

  return (
    <div data-ui="avatar-group" {...props}>
      {visible}
      {remaining > 0 && (
        <span data-ui="avatar" data-size="md" data-color="default">
          <span data-ui="avatar-fallback">+{remaining}</span>
        </span>
      )}
    </div>
  );
}
