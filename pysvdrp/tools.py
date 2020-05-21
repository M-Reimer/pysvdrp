def set_channel_position(self, sourceid, targetid, place_after = False, allow_breaking_groups = False):
    """
    Changes a channel's position in the channel list.

    sourceid: channel id of the channel to move
    targetid: channel id of the target to move the channel to
    place_after: sourceid is moved behind targetid if this is True
    allow_breaking_groups: If this is set to True groups can be emptied
    """
    # Get a channel list first
    channels = self.list_channels(True)

    # Get current list positions of the given items. Do exception handling here
    # as we don't know if the given values are valid.
    try:
        sourceindex = channels.find_by_channelid(sourceid)
    except ValueError as e:
        raise SVDRPError("Source id " + sourceid + "invalid!", 550) from e
    try:
        targetindex = channels.find_by_channelid(targetid)
    except ValueError as e:
        raise SVDRPError("Target id " + targetid + "invalid!", 550) from e

    # Group emptying protection. Check the surroundings
    if not allow_breaking_groups:
        groupex = SVDRPError("Moving this channel would empty a group which is not allowed!", 550)
        if sourceindex == 0:
            if channels[1].groupsep:
                raise groupex
        elif sourceindex == len(channels) - 1:
            if channels[-2].groupsep:
                raise groupex
        elif channels[sourceindex - 1].groupsep and \
             channels[sourceindex + 1].groupsep:
            raise groupex

    # We allow our own group separator channel IDs here. So translate their
    # positions to something VDR understands
    if channels[sourceindex].groupsep:
        raise SVDRPError("It is not allowed to move group separators!", 550)
    if channels[targetindex].groupsep:
        if place_after:
            targetindex += 1
            place_after = False
        else:
            targetindex -= 1
            place_after = True
        targetid = channels[targetindex].channelid

    # Where our channel lands depends on several things like:
    # - Is channel moved from above or from below?
    # - There is a bug in VDR 2.4.1 which may place the channel one off
    # So always place the channel to the target reference first. This
    # should bring us at least next to the wanted position
    sourcenumber = channels[sourceindex].number
    targetnumber = channels[targetindex].number
    self.move_channel(sourcenumber, targetnumber)

    # Now recheck where our source and our target are.
    channels = self._svdrp.list_channels(True)
    sourceindex = channels.find_by_channelid(sourceid)
    targetindex = channels.find_by_channelid(targetid)

    # If the order is wrong, then swap them
    if (sourceindex < targetindex and place_after) or \
       (targetindex < sourceindex and not place_after):
        sourcenumber = channels[sourceindex].number
        targetnumber = channels[targetindex].number
        self.move_channel(sourcenumber, targetnumber)
