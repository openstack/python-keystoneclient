

from keystoneclient import base


class Policy(base.Resource):
    """Represents an Identity policy.

    Attributes:
        * id: a uuid that identifies the policy
        * blob: a policy document (blob)
        * type: the mime type of the policy blob

    """
    def update(self, blob=None, type=None):
        kwargs = {
            'blob': blob if blob is not None else self.blob,
            'type': type if type is not None else self.type,
        }

        try:
            retval = self.manager.update(self.id, **kwargs)
            self = retval
        except Exception:
            retval = None

        return retval


class PolicyManager(base.ManagerWithFind):
    """Manager class for manipulating Identity policies."""
    resource_class = Policy
    collection_key = 'policies'
    key = 'policy'

    def create(self, blob, tenant_id, type):
        """
        Create a Policy.
        """
        params = {"policy": {"type": type if type else 'application/json',
                           "role_id": tenant_id,
                           "blob": blob,}}
        print params
        return self._create('/policies', params, "policy")

    def get(self, policy):
        return self._get("/policies/%s" % base.getid(policy), "policy")

    def get_role_policy(self, role):
        return self._get("/policies/role/%s" % base.getid(role), "policy")

    def delete(self, policy):
        """
        Delete a policy.
        """
        return self._delete("/policies/%s" % base.getid(policy))

    def list(self):
        return self._list("/policies","policies")
