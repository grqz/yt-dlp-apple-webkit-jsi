#ifndef COMMON_H
# if !defined(inline) && !defined(__cplusplus)
#  if defined(__STDC_VERSION__) && __STDC_VERSION__>=199901L
   /* just use inline */
#   define common_inline inline
#  elif defined(__GNUC__) && __GNUC__>=2
#   define common_inline __inline__
#  elif defined(_MSC_VER)
  /*
   * Visual Studio: inline is available in C++ only, however
   * __inline is available for C, see
   * http://msdn.microsoft.com/en-us/library/z8y1yy88.aspx
   */
#   define common_inline __inline
#  else
#   define common_inline
#  endif
# else
#  define common_inline inline
# endif
#endif /* COMMON_H */
