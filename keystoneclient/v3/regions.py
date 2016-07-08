# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from keystoneclient import base


class Region(base.Resource):
    """Represents a Catalog region.

    Attributes:
        * id: a string that identifies the region.
        * description: a string that describes the region.
        * parent_region_id: a pre-existing region in the backend or its ID
                            field. Allows for hierarchical region organization.
        * enabled: determines whether the endpoint appears in the catalog.
    """

    pass


class RegionManager(base.CrudManager):
    """Manager class for manipulating Identity regions."""

    resource_class = Region
    collection_key = 'regions'
    key = 'region'

    def create(self, id=None, description=None, enabled=True,
               parent_region=None, **kwargs):
        """Create a region.

        :param str id: the unique identifier of the region. If not specified an
                       ID will be created by the server.
        :param str description: the description of the region.
        :param bool enabled: whether the region is enabled or not, determining
                             if it appears in the catalog.
        :param parent_region: the parent of the region in the hierarchy.
        :type parent_region: str or :class:`keystoneclient.v3.regions.Region`
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the created region returned from server.
        :rtype: :class:`keystoneclient.v3.regions.Region`

        """
        return super(RegionManager, self).create(
            id=id, description=description, enabled=enabled,
            parent_region_id=base.getid(parent_region), **kwargs)

    def get(self, region):
        """Retrieve a region.

        :param region: the region to be retrieved from the server.
        :type region: str or :class:`keystoneclient.v3.regions.Region`

        :returns: the specified region returned from server.
        :rtype: :class:`keystoneclient.v3.regions.Region`

        """
        return super(RegionManager, self).get(
            region_id=base.getid(region))

    def list(self, **kwargs):
        """List regions.

        :param kwargs: any attributes provided will filter regions on.

        :returns: a list of regions.
        :rtype: list of :class:`keystoneclient.v3.regions.Region`.

        """
        return super(RegionManager, self).list(
            **kwargs)

    def update(self, region, description=None, enabled=None,
               parent_region=None, **kwargs):
        """Update a region.

        :param region: the region to be updated on the server.
        :type region: str or :class:`keystoneclient.v3.regions.Region`
        :param str description: the new description of the region.
        :param bool enabled: determining if the region appears in the catalog
                             by enabling or disabling it.
        :param parent_region: the new parent of the region in the hierarchy.
        :type parent_region: str or :class:`keystoneclient.v3.regions.Region`
        :param kwargs: any other attribute provided will be passed to server.

        :returns: the updated region returned from server.
        :rtype: :class:`keystoneclient.v3.regions.Region`

        """
        return super(RegionManager, self).update(
            region_id=base.getid(region),
            description=description,
            enabled=enabled,
            parent_region_id=base.getid(parent_region),
            **kwargs)

    def delete(self, region):
        """Delete a region.

        :param region: the region to be deleted on the server.
        :type region: str or :class:`keystoneclient.v3.regions.Region`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        return super(RegionManager, self).delete(
            region_id=base.getid(region))
