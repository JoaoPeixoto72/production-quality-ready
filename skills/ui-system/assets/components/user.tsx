import * as React from 'react';
import { Avatar, type AvatarProps } from './avatar';

export interface UserProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  description?: string;
  avatarProps?: Partial<AvatarProps>;
}

export const User = React.forwardRef<HTMLDivElement, UserProps>(
  ({ name, description, avatarProps, ...props }, ref) => {
    return (
      <div ref={ref} data-ui="user" {...props}>
        <Avatar name={name} {...avatarProps} />
        <div data-ui="user-info">
          <span data-ui="user-name">{name}</span>
          {description && <span data-ui="user-description">{description}</span>}
        </div>
      </div>
    );
  }
);

User.displayName = 'User';
