# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
from django.dispatch import receiver

from likes.exceptions import CannotVoteException
from likes.signals import can_vote_test

from secretballot.middleware import SecretBallotIpUseragentMiddleware


class SecretBallotUserMiddleware(SecretBallotIpUseragentMiddleware):

    def generate_token(self, request):
        if request.user.is_authenticated:
            return request.user.username
        else:
            return None


@receiver(can_vote_test)
def can_vote(instance, request, **kwargs):
    if not instance.question.competition.is_actual():
        raise CannotVoteException
