"""verify code attempts

Revision ID: 9077654efec6
Revises: ea70af22e20c
Create Date: 2023-05-22 22:39:34.092390

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9077654efec6'
down_revision = 'ea70af22e20c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('verify_codes', sa.Column('attempts', sa.SmallInteger(), nullable=False, server_default='5'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('verify_codes', 'attempts')
    # ### end Alembic commands ###