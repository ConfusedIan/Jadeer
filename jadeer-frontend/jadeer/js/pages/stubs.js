(function(){
  const { go } = window.JadeerRouter;
  const { register } = window.JadeerRouter;
  const { getToken } = window.JadeerAPI;
  const { currentRole } = window.JadeerAuth;

  // Root redirect
  register('/', () => {
    go(getToken()
      ? (currentRole() === 'employer' ? '/employer' : '/dashboard')
      : '/login');
  });
})();
