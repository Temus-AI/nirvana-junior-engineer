export default function NavBar() {
  return (
    <>
      <div
        className="mx-auto mt-[10px] flex h-16 w-full max-w-screen-xl items-center
         justify-between bg-white p-6 transition-all"
      >
        <div className="flex lg:flex-1">
          <img
            src="/temus.svg"
            alt="Temus logo"
            width="110"
            height="37"
            className="mr-2 rounded-sm"
          />
        </div>
      </div>
    </>
  )
}
